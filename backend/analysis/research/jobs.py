import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.db import close_old_connections, transaction
from django.utils import timezone

from analysis.conversation.streaming import (
    LEASE_SECONDS,
    _create_event,
    _lock_operation,
    claim_operation,
    fail_owned_operation,
    publish_owned_event,
    renew_operation_lease,
)
from analysis.models import (
    EvidenceClaim,
    Product,
    ResearchJob,
    SourcePolicy,
    SourceSnapshot,
    StreamOperation,
    Variant,
)


DEFAULT_LIMITS = {
    "max_domains": 3,
    "max_pages_per_domain": 5,
    "max_redirects_per_request": 2,
    "max_total_requests": 20,
    "max_decoded_bytes_per_page": 2 * 1024 * 1024,
    "request_timeout_seconds": 20,
    "job_deadline_seconds": 60,
    "outbound_concurrency_per_process": 2,
    "min_domain_interval_ms": 1000,
}

FIXTURE_CATALOG = {
    "synthetic-electronics-v1": {
        "role": "MANUFACTURER", "brand": "نمونه", "model": "گوشی آزمایشی E1",
        "identifier": "SYN-E1-256", "claims": {"capacity_gb": 256, "ram_gb": 8},
    },
    "synthetic-appliance-v1": {
        "role": "MANUFACTURER", "brand": "نمونه", "model": "قهوه‌ساز آزمایشی A1",
        "identifier": "SYN-A1", "claims": {"water_tank_l": "1.8", "voltage_v": 230},
    },
    "synthetic-sports-v1": {
        "role": "MANUFACTURER", "brand": "نمونه", "model": "کفش آزمایشی S1",
        "identifier": "SYN-S1-42", "claims": {"size_eu": 42, "condition": "NEW"},
    },
}

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="copilot-research")
_capacity = threading.BoundedSemaphore(4)
_worker_identity = f"research-{os.getpid()}-{id(_executor):x}"


def canonical_research_hash(expected_revision, source_ids, mode):
    value = {"expected_brief_revision": expected_revision, "source_ids": sorted(source_ids), "mode": mode}
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


@transaction.atomic
def create_research_job(*, conversation, idempotency_key, request_hash, source_ids, mode):
    from analysis.models import Conversation, GuestContext

    GuestContext.objects.select_for_update().get(id=conversation.guest_context_id)
    locked = Conversation.objects.select_for_update().get(id=conversation.id)
    existing_operation = StreamOperation.objects.filter(
        conversation=locked, idempotency_key=idempotency_key, operation_kind="RESEARCH"
    ).first()
    if existing_operation:
        if existing_operation.request_hash != request_hash:
            raise ValueError("IDEMPOTENCY_CONFLICT")
        return existing_operation.research_job, True
    if ResearchJob.objects.filter(
        conversation__guest_context=locked.guest_context,
        status__in=["PENDING", "RUNNING"],
    ).exists():
        raise ValueError("RESEARCH_LIMIT_REACHED")
    operation = StreamOperation.objects.create(
        conversation=locked,
        operation_kind="RESEARCH",
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        expected_brief_revision=locked.brief_revision,
    )
    job = ResearchJob.objects.create(
        conversation=locked,
        operation=operation,
        brief_revision=locked.brief_revision,
        generation_epoch=locked.generation_epoch,
        request_hash=request_hash,
        mode=mode,
        source_ids=list(source_ids),
        limits=dict(DEFAULT_LIMITS),
        total_units=len(source_ids),
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
        release_research_slot()
        return False
    return True


def publish_research_progress(job_id, lease_owner, *, stage, completed, total):
    job_ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
    if job_ref is None:
        return False
    with transaction.atomic():
        now = timezone.now()
        conversation, operation = _lock_operation(job_ref["operation_id"])
        if (
            operation is None
            or operation.status != "RUNNING"
            or operation.lease_owner != lease_owner
            or operation.lease_expires_at is None
            or operation.lease_expires_at <= now
            or conversation.expires_at <= now
            or conversation.brief_revision != operation.expected_brief_revision
            or operation.cancel_requested_at
        ):
            return False
        job = ResearchJob.objects.select_for_update().get(id=job_id, operation=operation)
        if completed < job.completed_units or completed > total or total != job.total_units:
            return False
        _create_event(
            operation,
            conversation,
            "research.progress",
            {"research_job_id": str(job.id), "stage": stage, "completed": completed, "total": total},
            now,
        )
        operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        operation.save(update_fields=["next_sequence", "lease_expires_at", "updated_at"])
        job.status = "RUNNING"
        job.stage = stage
        job.completed_units = completed
        if job.started_at is None:
            job.started_at = now
        job.save(update_fields=["status", "stage", "completed_units", "started_at"])
        return True


def complete_research_job(job_id, lease_owner, *, coverage, outcome):
    job_ref = ResearchJob.objects.filter(id=job_id).values("operation_id").first()
    if job_ref is None:
        return False
    with transaction.atomic():
        now = timezone.now()
        conversation, operation = _lock_operation(job_ref["operation_id"])
        if (
            operation is None
            or operation.status != "RUNNING"
            or operation.lease_owner != lease_owner
            or operation.lease_expires_at is None
            or operation.lease_expires_at <= now
            or conversation.expires_at <= now
            or conversation.brief_revision != operation.expected_brief_revision
            or operation.cancel_requested_at
        ):
            return False
        job = ResearchJob.objects.select_for_update().get(id=job_id, operation=operation)
        _create_event(
            operation,
            conversation,
            "operation.completed",
            {"research_job_id": str(job.id), "outcome": outcome, "coverage": coverage},
            now,
        )
        operation.status = "COMPLETED"
        operation.terminal_code = None
        operation.completed_at = now
        operation.lease_owner = None
        operation.lease_expires_at = None
        operation.save(update_fields=[
            "next_sequence", "status", "terminal_code", "completed_at",
            "lease_owner", "lease_expires_at", "updated_at",
        ])
        job.status = outcome
        job.stage = "COMPLETED"
        job.coverage = coverage
        job.completed_at = now
        job.save(update_fields=["status", "stage", "coverage", "completed_at"])
        return True


def _persist_fixture(job, fixture_id):
    item = FIXTURE_CATALOG[fixture_id]
    policy, _ = SourcePolicy.objects.get_or_create(
        hostname="synthetic.beforebuy.invalid",
        defaults={
            "allowed_path_prefixes": [],
            "redirect_hostnames": [],
            "source_role": "MANUFACTURER",
            "readiness": "SYNTHETIC_FIXTURE",
            "live_enabled": False,
            "access_notes": "Project-authored synthetic fixture; not a public source.",
        },
    )
    now = timezone.now()
    payload = json.dumps(item, ensure_ascii=False, sort_keys=True).encode()
    snapshot = SourceSnapshot.objects.create(
        research_job=job,
        source_policy=policy,
        canonical_url=None,
        fixture_label=fixture_id,
        source_role=item["role"],
        retrieval_time=now,
        status="EXTRACTED",
        content_type="application/json",
        response_bytes=len(payload),
        fingerprint=hashlib.sha256(payload).hexdigest(),
        extractor_version="SYNTHETIC-v1",
        raw_content=payload,
        raw_expires_at=now + timedelta(hours=24),
    )
    product = Product.objects.create(brand=item["brand"], model_name=item["model"])
    variant = Variant.objects.create(
        product=product,
        canonical_identifier=item["identifier"],
        identifiers={"synthetic_id": item["identifier"]},
        attributes=item["claims"],
    )
    for field, value in item["claims"].items():
        EvidenceClaim.objects.create(
            snapshot=snapshot,
            variant=variant,
            field=field,
            normalized_value={"value": value},
            source_location=f"synthetic:{field}",
            evidence_status="SUPPORTED",
        )
    return snapshot


def _reuse_cached_fixture(job, fixture_id):
    cached = SourceSnapshot.objects.filter(
        research_job__conversation=job.conversation,
        fixture_label=fixture_id,
        raw_expires_at__gt=timezone.now(),
        raw_content__isnull=False,
        status__in=["EXTRACTED", "CACHE_HIT"],
    ).exclude(research_job=job).order_by("-retrieval_time").first()
    if cached is None:
        return None
    clone = SourceSnapshot.objects.create(
        research_job=job,
        source_policy=cached.source_policy,
        canonical_url=cached.canonical_url,
        fixture_label=cached.fixture_label,
        source_role=cached.source_role,
        retrieval_time=cached.retrieval_time,
        status="CACHE_HIT",
        http_status=cached.http_status,
        content_type=cached.content_type,
        response_bytes=cached.response_bytes,
        fingerprint=cached.fingerprint,
        extractor_version=cached.extractor_version,
        raw_content=cached.raw_content,
        raw_expires_at=cached.raw_expires_at,
    )
    for claim in cached.claims.all():
        EvidenceClaim.objects.create(
            snapshot=clone,
            variant=claim.variant,
            field=claim.field,
            normalized_value=claim.normalized_value,
            source_location=claim.source_location,
            supporting_excerpt=claim.supporting_excerpt,
            evidence_status=claim.evidence_status,
        )
    return clone


def perform_research(job_id, lease_owner):
    job = ResearchJob.objects.get(id=job_id)
    extracted = []
    blocked = []
    for index, source_id in enumerate(job.source_ids, start=1):
        if not renew_operation_lease(job.operation_id, lease_owner):
            return False
        if job.mode == "FIXTURE" and source_id in FIXTURE_CATALOG:
            _reuse_cached_fixture(job, source_id) or _persist_fixture(job, source_id)
            extracted.append(source_id)
        else:
            blocked.append(source_id)
        if not publish_research_progress(
            job.id, lease_owner, stage="EXTRACT", completed=index, total=job.total_units
        ):
            return False
    coverage = {"extracted": extracted, "blocked": blocked, "mode": job.mode}
    if extracted and blocked:
        outcome = "PARTIAL_SUCCESS"
    elif extracted:
        outcome = "SUCCESS"
    else:
        outcome = "NO_SUPPORTED_SOURCES"
    return complete_research_job(job.id, lease_owner, coverage=coverage, outcome=outcome)


def execute_research_job(job_id, *, worker_identity=None, release_slot=True):
    owner = worker_identity or _worker_identity
    close_old_connections()
    try:
        job = ResearchJob.objects.get(id=job_id)
        if not claim_operation(job.operation_id, owner):
            return
        if not publish_owned_event(
            job.operation_id,
            owner,
            "operation.started",
            {"kind": "RESEARCH", "research_job_id": str(job.id), "limits": job.limits, "mode": job.mode},
        ):
            return
        perform_research(job.id, owner)
    except Exception:
        try:
            job = ResearchJob.objects.get(id=job_id)
            if fail_owned_operation(job.operation_id, owner, "RESEARCH_FAILED"):
                ResearchJob.objects.filter(id=job.id).update(
                    status="FAILED", terminal_code="RESEARCH_FAILED", completed_at=timezone.now()
                )
        except ResearchJob.DoesNotExist:
            pass
    finally:
        close_old_connections()
        if release_slot:
            release_research_slot()
