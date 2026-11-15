import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from urllib.parse import urlsplit

from django.db import close_old_connections, transaction
from django.utils import timezone

from analysis.conversation.streaming import (
    LEASE_SECONDS, _create_event, _lock_operation, _terminalize_locked,
    claim_operation, fail_unstarted_operation, publish_owned_event,
    reconcile_stale_operation, renew_operation_lease,
)
from analysis.models import (
    Conversation, EvidenceClaim, GuestContext, Offer, Product, ResearchJob,
    SourcePolicy, SourceSnapshot, StreamOperation, Variant,
)
from analysis.research.extractors import EXTRACTOR_VERSION, ExtractionError, extract_product_document
from analysis.research.fetch import FetchBudget, FetchError, FetchPolicy, SafeFetcher
from analysis.research.identity import IdentityConflict, VariantIdentity, reconcile_variant


DEFAULT_LIMITS = {
    "max_domains": 3, "max_pages_per_domain": 5, "max_redirects_per_request": 2,
    "max_total_requests": 20, "max_decoded_bytes_per_page": 2 * 1024 * 1024,
    "max_wire_bytes_per_page": 2 * 1024 * 1024, "request_timeout_seconds": 20,
    "job_deadline_seconds": 60, "outbound_concurrency_per_process": 2,
    "min_domain_interval_ms": 1000,
}

FIXTURE_CATALOG = {
    "synthetic-electronics-v1": {"role": "MANUFACTURER", "brand": "نمونه", "model": "گوشی آزمایشی E1", "identifier": "SYN-E1-256", "claims": {"capacity_gb": 256, "ram_gb": 8}},
    "synthetic-appliance-v1": {"role": "MANUFACTURER", "brand": "نمونه", "model": "قهوه‌ساز آزمایشی A1", "identifier": "SYN-A1", "claims": {"water_tank_l": "1.8", "voltage_v": 230}},
    "synthetic-sports-v1": {"role": "MANUFACTURER", "brand": "نمونه", "model": "کفش آزمایشی S1", "identifier": "SYN-S1-42", "claims": {"size_eu": 42, "condition": "NEW"}},
}

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="copilot-research")
_capacity = threading.BoundedSemaphore(4)
_worker_identity = f"research-{os.getpid()}-{id(_executor):x}"


def normalize_targets(targets=None, source_ids=None):
    if targets is None:
        targets = [{"source_id": value, "url": None} for value in (source_ids or [])]
    return [{"source_id": item["source_id"], "url": item.get("url")} for item in targets]


def canonical_research_hash(expected_revision, targets, mode):
    normalized = normalize_targets(targets=targets)
    value = {"expected_brief_revision": expected_revision,
             "targets": sorted(normalized, key=lambda item: (item["source_id"], item.get("url") or "")),
             "mode": mode}
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def _validate_locked_targets(targets, mode):
    if mode == "FIXTURE":
        return
    policies = {
        item.hostname: item
        for item in SourcePolicy.objects.select_for_update().filter(
            hostname__in=[target["source_id"] for target in targets]
        )
    }
    for target in targets:
        policy = policies.get(target["source_id"])
        url = target.get("url")
        if policy is None:
            raise ValueError("SOURCE_NOT_APPROVED")
        try:
            parts = urlsplit(url)
        except (TypeError, ValueError) as exc:
            raise ValueError("TARGET_URL_INVALID") from exc
        if not url or (parts.hostname or "").rstrip(".").lower() != policy.hostname:
            raise ValueError("TARGET_SOURCE_MISMATCH")


@transaction.atomic
def create_research_job(*, conversation=None, conversation_id=None, guest=None, expected_revision=None,
                        idempotency_key, request_hash, targets=None, source_ids=None, mode):
    conversation_id = conversation_id or conversation.id
    guest = guest or conversation.guest_context
    GuestContext.objects.select_for_update().get(id=guest.id)
    locked = Conversation.objects.select_for_update().get(id=conversation_id, guest_context=guest)
    existing_operation = StreamOperation.objects.filter(
        conversation=locked, idempotency_key=idempotency_key, operation_kind="RESEARCH"
    ).first()
    if existing_operation:
        if existing_operation.request_hash != request_hash:
            raise ValueError("IDEMPOTENCY_CONFLICT")
        return existing_operation.research_job, True
    now = timezone.now()
    expected_revision = locked.brief_revision if expected_revision is None else expected_revision
    if locked.expires_at <= now:
        raise ValueError("CONVERSATION_EXPIRED")
    if locked.brief_revision != expected_revision:
        raise ValueError("STALE_BRIEF_REVISION")
    if not locked.brief.confirmed:
        raise ValueError("BRIEF_NOT_CONFIRMED")
    normalized = normalize_targets(targets, source_ids)
    if len({item["source_id"] for item in normalized}) > DEFAULT_LIMITS["max_domains"]:
        raise ValueError("DOMAIN_BUDGET_EXCEEDED")
    _validate_locked_targets(normalized, mode)
    for active in ResearchJob.objects.filter(
        conversation__guest_context=locked.guest_context, status__in=["PENDING", "RUNNING"]
    ).select_related("operation"):
        reconciled = reconcile_stale_operation(active.operation_id)
        if reconciled and reconciled.status in {"PENDING", "RUNNING"}:
            raise ValueError("RESEARCH_LIMIT_REACHED")
        _sync_terminal_job(active.id, reconciled)
    operation = StreamOperation.objects.create(
        conversation=locked, operation_kind="RESEARCH", idempotency_key=idempotency_key,
        request_hash=request_hash, expected_brief_revision=expected_revision,
    )
    job = ResearchJob.objects.create(
        conversation=locked, operation=operation, brief_revision=expected_revision,
        generation_epoch=locked.generation_epoch, request_hash=request_hash, mode=mode,
        source_ids=[item["source_id"] for item in normalized], targets=normalized,
        limits=dict(DEFAULT_LIMITS), total_units=len(normalized),
    )
    return job, False


def reserve_research_slot():
    return _capacity.acquire(blocking=False)


def release_research_slot():
    _capacity.release()


def submit_research_reserved(job_id):
    try:
        _executor.submit(execute_research_job, job_id)
    except Exception:
        with transaction.atomic():
            if fail_unstarted_operation(ResearchJob.objects.get(id=job_id).operation_id):
                ResearchJob.objects.filter(id=job_id).update(
                    status="FAILED", stage="FAILED", terminal_code="SUBMISSION_FAILED", completed_at=timezone.now())
        release_research_slot()
        return False
    return True


def _valid_worker(conversation, operation, job, lease_owner, now):
    return (operation.status == "RUNNING" and operation.lease_owner == lease_owner
            and operation.lease_expires_at is not None and operation.lease_expires_at > now
            and not operation.cancel_requested_at and conversation.expires_at > now
            and conversation.brief_revision == operation.expected_brief_revision == job.brief_revision
            and conversation.generation_epoch == job.generation_epoch)


def publish_research_progress(job_id, lease_owner, *, stage, completed, total):
    ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
    if ref is None:
        return False
    with transaction.atomic():
        now = timezone.now()
        conversation, operation = _lock_operation(ref["operation_id"])
        if operation is None:
            return False
        job = ResearchJob.objects.select_for_update().get(id=job_id, operation=operation)
        if not _valid_worker(conversation, operation, job, lease_owner, now):
            return False
        if completed < job.completed_units or completed > total or total != job.total_units:
            return False
        _create_event(operation, conversation, "research.progress", {
            "research_job_id": str(job.id), "stage": stage, "completed": completed, "total": total}, now)
        operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        operation.save(update_fields=["next_sequence", "lease_expires_at", "updated_at"])
        job.status, job.stage, job.completed_units = "RUNNING", stage, completed
        job.started_at = job.started_at or now
        job.save(update_fields=["status", "stage", "completed_units", "started_at"])
        return True


def _identity_for(extraction):
    brand = extraction.product.brand or "UNKNOWN"
    incoming = VariantIdentity(brand, extraction.product.model_name, extraction.variant.identifiers,
                               extraction.variant.attributes, False, "NEW")
    for variant in Variant.objects.select_related("product").filter(
        product__brand__iexact=brand, product__model_name__iexact=extraction.product.model_name
    ):
        existing = VariantIdentity(variant.product.brand, variant.product.model_name, variant.identifiers,
                                   variant.attributes, variant.bundle, variant.condition)
        try:
            if reconcile_variant(existing, incoming).status == "MATCH":
                return variant
        except IdentityConflict:
            continue
    product = Product.objects.create(brand=brand, model_name=extraction.product.model_name)
    identifiers = extraction.variant.identifiers
    return Variant.objects.create(product=product, canonical_identifier=next(iter(identifiers.values()), None),
                                  identifiers=identifiers, attributes=extraction.variant.attributes)


def _persist_extraction(job, policy, candidate, now):
    result = candidate["extraction"]
    snapshot = SourceSnapshot.objects.create(
        research_job=job, source_policy=policy, canonical_url=candidate["url"], fixture_label=None,
        source_role=policy.source_role, retrieval_time=candidate["retrieved_at"], status="EXTRACTED",
        http_status=candidate["status"], content_type=candidate["content_type"], response_bytes=len(candidate["body"]),
        fingerprint=hashlib.sha256(candidate["body"]).hexdigest(), extractor_version=EXTRACTOR_VERSION,
        raw_content=candidate["body"], raw_expires_at=now + timedelta(hours=24))
    variant = _identity_for(result)
    if result.offer:
        Offer.objects.create(snapshot=snapshot, variant=variant, item_price_minor=result.offer.item_price_minor,
                             currency=result.offer.currency, shipping_minor=result.offer.shipping_minor,
                             total_payable_minor=result.offer.total_payable_minor, seller=result.offer.seller,
                             availability=result.offer.availability, observed_at=candidate["retrieved_at"])
    for claim in result.claims:
        EvidenceClaim.objects.create(snapshot=snapshot, variant=variant, field=claim.field,
                                     normalized_value={"value": claim.value}, source_location=claim.source_location,
                                     evidence_status="SUPPORTED")
    return snapshot


def _persist_fixture(job, policy, candidate, now):
    item, payload = candidate["item"], candidate["body"]
    snapshot = SourceSnapshot.objects.create(
        research_job=job, source_policy=policy, canonical_url=None, fixture_label=candidate["source_id"],
        source_role=item["role"], retrieval_time=candidate["retrieved_at"], status="EXTRACTED",
        content_type="application/json", response_bytes=len(payload), fingerprint=hashlib.sha256(payload).hexdigest(),
        extractor_version="SYNTHETIC-v1", raw_content=payload, raw_expires_at=now + timedelta(hours=24))
    product = Product.objects.create(brand=item["brand"], model_name=item["model"])
    variant = Variant.objects.create(product=product, canonical_identifier=item["identifier"],
                                     identifiers={"synthetic_id": item["identifier"]}, attributes=item["claims"])
    for field, value in item["claims"].items():
        EvidenceClaim.objects.create(snapshot=snapshot, variant=variant, field=field,
                                     normalized_value={"value": value}, source_location=f"synthetic:{field}",
                                     evidence_status="SUPPORTED")
    return snapshot


def _persist_cache(job, cached):
    clone = SourceSnapshot.objects.create(
        research_job=job, source_policy=cached.source_policy, canonical_url=cached.canonical_url,
        fixture_label=cached.fixture_label, source_role=cached.source_role, retrieval_time=cached.retrieval_time,
        status="CACHE_HIT", http_status=cached.http_status, content_type=cached.content_type,
        response_bytes=cached.response_bytes, fingerprint=cached.fingerprint, extractor_version=cached.extractor_version,
        raw_content=cached.raw_content, raw_expires_at=cached.raw_expires_at)
    for offer in cached.offers.all():
        Offer.objects.create(snapshot=clone, variant=offer.variant, item_price_minor=offer.item_price_minor,
                             currency=offer.currency, shipping_minor=offer.shipping_minor,
                             total_payable_minor=offer.total_payable_minor, seller=offer.seller,
                             warranty=offer.warranty, registration=offer.registration,
                             availability=offer.availability, observed_at=offer.observed_at)
    for claim in cached.claims.all():
        EvidenceClaim.objects.create(snapshot=clone, variant=claim.variant, field=claim.field,
                                     normalized_value=claim.normalized_value, source_location=claim.source_location,
                                     supporting_excerpt=claim.supporting_excerpt, evidence_status=claim.evidence_status)
    return clone


def publish_evidence_unit(job_id, lease_owner, candidate, budget, *, completed, before_complete=None):
    ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
    if ref is None:
        return False
    with transaction.atomic():
        now = timezone.now()
        conversation, operation = _lock_operation(ref["operation_id"])
        if operation is None:
            return False
        job = ResearchJob.objects.select_for_update().get(id=job_id, operation=operation)
        if not _valid_worker(conversation, operation, job, lease_owner, now):
            return False
        policy = SourcePolicy.objects.select_for_update().get(id=candidate["policy_id"])
        if job.mode == "LIVE" and candidate["kind"] != "failure" and not policy.live_enabled:
            return False
        if candidate["kind"] == "fixture":
            snapshot = _persist_fixture(job, policy, candidate, now)
        elif candidate["kind"] == "cache":
            cached = SourceSnapshot.objects.select_for_update().get(
                id=candidate["snapshot_id"], research_job__conversation=conversation,
                raw_expires_at__gt=now, raw_content__isnull=False)
            snapshot = _persist_cache(job, cached)
        elif candidate["kind"] == "extraction":
            snapshot = _persist_extraction(job, policy, candidate, now)
        else:
            payload = candidate.get("body", b"")
            snapshot = SourceSnapshot.objects.create(
                research_job=job, source_policy=policy, canonical_url=candidate.get("url"),
                fixture_label=candidate.get("fixture_label"), source_role=policy.source_role,
                retrieval_time=candidate["retrieved_at"], status=candidate["status"], response_bytes=len(payload),
                fingerprint=hashlib.sha256(payload).hexdigest(), failure_code=candidate["failure_code"],
                raw_content=None, raw_expires_at=now)
        job.request_count, job.decoded_bytes = budget.request_count, budget.decoded_bytes
        job.wire_bytes, job.redirect_count = budget.wire_bytes, budget.redirect_count
        job.completed_units, job.stage, job.status = completed, "EXTRACT", "RUNNING"
        job.started_at = job.started_at or now
        _create_event(operation, conversation, "evidence.published", {
            "research_job_id": str(job.id), "snapshot_id": str(snapshot.id),
            "source_id": candidate["source_id"], "status": snapshot.status}, now)
        _create_event(operation, conversation, "research.progress", {
            "research_job_id": str(job.id), "stage": "EXTRACT", "completed": completed,
            "total": job.total_units}, now)
        if before_complete:
            before_complete()
        operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        operation.save(update_fields=["next_sequence", "lease_expires_at", "updated_at"])
        job.save(update_fields=["request_count", "decoded_bytes", "wire_bytes", "redirect_count",
                                "completed_units", "stage", "status", "started_at"])
        return True


def complete_research_job(job_id, lease_owner, *, coverage, outcome):
    ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
    if ref is None:
        return False
    with transaction.atomic():
        now = timezone.now()
        conversation, operation = _lock_operation(ref["operation_id"])
        if operation is None:
            return False
        job = ResearchJob.objects.select_for_update().get(id=job_id, operation=operation)
        if not _valid_worker(conversation, operation, job, lease_owner, now):
            return False
        _create_event(operation, conversation, "operation.completed", {
            "research_job_id": str(job.id), "outcome": outcome, "coverage": coverage}, now)
        operation.status, operation.terminal_code, operation.completed_at = "COMPLETED", None, now
        operation.lease_owner = operation.lease_expires_at = None
        operation.save(update_fields=["next_sequence", "status", "terminal_code", "completed_at",
                                      "lease_owner", "lease_expires_at", "updated_at"])
        job.status, job.stage, job.coverage, job.completed_at = outcome, "COMPLETED", coverage, now
        job.save(update_fields=["status", "stage", "coverage", "completed_at"])
        return True


def _fixture_policy():
    return SourcePolicy.objects.get_or_create(
        hostname="synthetic.beforebuy.invalid",
        defaults={"allowed_path_prefixes": [], "redirect_hostnames": [], "source_role": "MANUFACTURER",
                  "readiness": "SYNTHETIC_FIXTURE", "live_enabled": False,
                  "access_notes": "Project-authored synthetic fixture; not a public source."})[0]


def _cached_candidate(job, target):
    lookup = {"fixture_label": target["source_id"]} if job.mode == "FIXTURE" else {"canonical_url": target["url"]}
    cached = SourceSnapshot.objects.filter(
        research_job__conversation=job.conversation, raw_expires_at__gt=timezone.now(),
        raw_content__isnull=False, status__in=["EXTRACTED", "CACHE_HIT"], **lookup
    ).exclude(research_job=job).order_by("-retrieval_time").first()
    if cached:
        return {"kind": "cache", "source_id": target["source_id"], "policy_id": cached.source_policy_id,
                "snapshot_id": cached.id}
    return None


def _policy_to_fetch(policy, limits):
    return FetchPolicy(
        hostname=policy.hostname, allowed_path_prefixes=tuple(policy.allowed_path_prefixes),
        redirect_hostnames=tuple(policy.redirect_hostnames), redirect_rules=policy.redirect_rules,
        allowed_ports=tuple(policy.allowed_ports), enabled=policy.live_enabled,
        max_redirects=limits["max_redirects_per_request"],
        max_decoded_bytes=limits["max_decoded_bytes_per_page"], max_wire_bytes=limits["max_wire_bytes_per_page"],
        request_timeout_seconds=limits["request_timeout_seconds"],
        min_interval_seconds=policy.min_interval_ms / 1000)


def perform_research(job_id, lease_owner, *, fetcher=None):
    job = ResearchJob.objects.select_related("conversation").get(id=job_id)
    targets = job.targets or normalize_targets(source_ids=job.source_ids)
    budget = FetchBudget(max_requests=job.limits["max_total_requests"],
                         max_pages_per_domain=job.limits["max_pages_per_domain"],
                         deadline_monotonic=time.monotonic() + job.limits["job_deadline_seconds"])
    fetcher = fetcher or SafeFetcher()
    extracted, blocked, failed = [], [], []
    for index, target in enumerate(targets, start=1):
        if not renew_operation_lease(job.operation_id, lease_owner):
            return False
        candidate = _cached_candidate(job, target)
        if candidate is None and job.mode == "FIXTURE" and target["source_id"] in FIXTURE_CATALOG:
            item = FIXTURE_CATALOG[target["source_id"]]
            body = json.dumps(item, ensure_ascii=False, sort_keys=True).encode()
            candidate = {"kind": "fixture", "source_id": target["source_id"], "policy_id": _fixture_policy().id,
                         "item": item, "body": body, "retrieved_at": timezone.now()}
        elif candidate is None and job.mode == "LIVE":
            policy = SourcePolicy.objects.filter(hostname=target["source_id"]).first()
            if policy and policy.live_enabled:
                try:
                    result = fetcher.fetch(target["url"], _policy_to_fetch(policy, job.limits), budget)
                    extraction = extract_product_document(result.body, source_url=result.url,
                                                          source_role=policy.source_role, retrieved_at=timezone.now())
                    candidate = {"kind": "extraction", "source_id": target["source_id"],
                                 "policy_id": policy.id, "url": result.url, "status": result.status,
                                 "content_type": result.content_type, "body": result.body,
                                 "retrieved_at": timezone.now(), "extraction": extraction}
                except (FetchError, ExtractionError) as exc:
                    code = getattr(exc, "code", str(exc))
                    candidate = {"kind": "failure", "source_id": target["source_id"], "policy_id": policy.id,
                                 "url": target["url"], "retrieved_at": timezone.now(),
                                 "status": "FAILED", "failure_code": code}
                    failed.append({"source_id": target["source_id"], "code": code})
            elif policy:
                candidate = {"kind": "failure", "source_id": target["source_id"], "policy_id": policy.id,
                             "url": target["url"], "retrieved_at": timezone.now(),
                             "status": "BLOCKED", "failure_code": "SOURCE_DISABLED"}
                blocked.append({"source_id": target["source_id"], "code": "SOURCE_DISABLED"})
        if candidate is None:
            policy = _fixture_policy()
            candidate = {"kind": "failure", "source_id": target["source_id"], "policy_id": policy.id,
                         "fixture_label": target["source_id"], "retrieved_at": timezone.now(),
                         "status": "BLOCKED", "failure_code": "SOURCE_NOT_SUPPORTED"}
            blocked.append({"source_id": target["source_id"], "code": "SOURCE_NOT_SUPPORTED"})
        if not renew_operation_lease(job.operation_id, lease_owner):
            return False
        if not publish_evidence_unit(job.id, lease_owner, candidate, budget, completed=index):
            return False
        if candidate["kind"] in {"fixture", "cache", "extraction"}:
            extracted.append(target["source_id"])
    coverage = {"extracted": extracted, "blocked": blocked, "failed": failed, "mode": job.mode}
    outcome = "PARTIAL_SUCCESS" if extracted and (blocked or failed) else "SUCCESS" if extracted else "NO_SUPPORTED_SOURCES"
    return complete_research_job(job.id, lease_owner, coverage=coverage, outcome=outcome)


def _sync_terminal_job(job_id, operation):
    if operation is None or operation.status not in {"FAILED", "CANCELLED", "INTERRUPTED"}:
        return
    ResearchJob.objects.filter(id=job_id, status__in=["PENDING", "RUNNING"]).update(
        status=operation.status, stage=operation.status, terminal_code=operation.terminal_code,
        completed_at=operation.completed_at or timezone.now())


def reconcile_research_job(job_id):
    job = ResearchJob.objects.select_related("operation").filter(id=job_id).first()
    if not job:
        return None
    operation = reconcile_stale_operation(job.operation_id)
    _sync_terminal_job(job.id, operation)
    return ResearchJob.objects.select_related("operation").get(id=job_id)


@transaction.atomic
def cancel_research_job(job_id):
    job = ResearchJob.objects.select_related("operation").get(id=job_id)
    now = timezone.now()
    conversation, operation = _lock_operation(job.operation_id)
    job = ResearchJob.objects.select_for_update().get(id=job_id)
    if operation.status in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
        return False, operation, job
    operation.cancel_requested_at = operation.cancel_requested_at or now
    _terminalize_locked(operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
                        "CANCELLED", "USER_REQUEST", now)
    operation.save(update_fields=["cancel_requested_at", "updated_at"])
    job.status, job.stage, job.terminal_code, job.completed_at = "CANCELLED", "CANCELLED", "USER_REQUEST", now
    job.save(update_fields=["status", "stage", "terminal_code", "completed_at"])
    return True, operation, job


def execute_research_job(job_id, *, worker_identity=None, release_slot=True):
    owner = worker_identity or _worker_identity
    close_old_connections()
    try:
        job = ResearchJob.objects.get(id=job_id)
        if not claim_operation(job.operation_id, owner):
            reconcile_research_job(job.id)
            return
        if not publish_owned_event(job.operation_id, owner, "operation.started", {
            "kind": "RESEARCH", "research_job_id": str(job.id), "limits": job.limits, "mode": job.mode}):
            return
        perform_research(job.id, owner)
    except Exception:
        with transaction.atomic():
            ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
            if ref:
                now = timezone.now()
                conversation, operation = _lock_operation(ref["operation_id"])
                job = ResearchJob.objects.select_for_update().get(id=job_id)
                if operation and operation.status == "RUNNING" and operation.lease_owner == owner:
                    _terminalize_locked(operation, conversation, "operation.failed", {"code": "RESEARCH_FAILED"},
                                        "FAILED", "RESEARCH_FAILED", now, publish=conversation.expires_at > now)
                    job.status, job.stage, job.terminal_code, job.completed_at = "FAILED", "FAILED", "RESEARCH_FAILED", now
                    job.save(update_fields=["status", "stage", "terminal_code", "completed_at"])
    finally:
        close_old_connections()
        if release_slot:
            release_research_slot()
