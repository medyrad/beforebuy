import re
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from analysis.conversation.serializers import serialize_operation
from analysis.conversation.streaming import TERMINAL
from analysis.guest import get_or_create_guest
from analysis.models import Conversation, ResearchJob
from analysis.research.jobs import (
    canonical_research_hash,
    cancel_research_job,
    create_research_job,
    normalize_targets,
    reconcile_research_job,
    release_research_slot,
    reserve_research_slot,
    submit_research_reserved,
)

from .base import CsrfProtectedAPIView
from .conversations import active_conversation, error
from .errors import CopilotUnavailable


def serialize_research_job(job):
    snapshots = job.snapshots.order_by("created_at")
    now = timezone.now()
    visible_offers = {}
    for snapshot in snapshots.select_related("source_policy").prefetch_related("offers__variant__product"):
        fresh_until = snapshot.retrieval_time + timedelta(seconds=snapshot.source_policy.freshness_seconds)
        state = ("SYNTHETIC" if snapshot.fixture_label and snapshot.extractor_version == "SYNTHETIC-v1"
                 else "CAPTURED_FIXTURE" if snapshot.fixture_label else "CACHE" if snapshot.status == "CACHE_HIT" else "LIVE")
        if state not in {"SYNTHETIC"} and fresh_until <= now:
            state = "STALE"
        for offer in snapshot.offers.all():
            seller_key = re.sub(r"\s+", " ", (offer.seller or "").strip()).casefold()
            key = (str(offer.variant_id), seller_key, offer.price_toman)
            item = {
                "id": str(offer.id), "variant_id": str(offer.variant_id),
                "product_name": offer.variant.product.model_name, "seller": offer.seller,
                "source_name": snapshot.source_policy.hostname, "source_url": snapshot.canonical_url,
                "merchant_url": offer.merchant_url, "item_price": offer.item_price_minor,
                "source_currency": offer.currency, "price_toman": offer.price_toman,
                "shipping_toman": offer.shipping_minor,
                "mandatory_charges_toman": offer.mandatory_charges_minor,
                "total_payable_toman": offer.total_payable_minor,
                "warranty": offer.warranty, "availability": offer.availability,
                "observation_kind": offer.observation_kind, "evidence_state": state,
                "observed_at": offer.observed_at.isoformat(), "fresh_until": fresh_until.isoformat(),
            }
            previous = visible_offers.get(key)
            if previous is None or (previous["observation_kind"] == "COMPARISON_OBSERVED"
                                    and item["observation_kind"] == "MERCHANT_PAGE_VERIFIED"):
                visible_offers[key] = item
    offers = sorted(
        visible_offers.values(),
        key=lambda item: (item["price_toman"] is None, item["price_toman"] or 0,
                          (item["seller"] or "").casefold(), item["observed_at"], item["id"]),
    )
    return {
        "id": str(job.id),
        "conversation_id": str(job.conversation_id),
        "operation_id": str(job.operation_id),
        "mode": job.mode,
        "fixture_labeled": job.mode == "FIXTURE",
        "status": job.status,
        "stage": job.stage,
        "completed": job.completed_units,
        "total": job.total_units,
        "request_count": job.request_count,
        "decoded_bytes": job.decoded_bytes,
        "wire_bytes": job.wire_bytes,
        "redirect_count": job.redirect_count,
        "targets": job.targets,
        "brief_revision": job.brief_revision,
        "current_for_brief": job.conversation.brief_revision == job.brief_revision,
        "coverage": job.coverage,
        "limits": job.limits,
        "offers": offers,
        "snapshots": [
            {
                "id": str(item.id),
                "source_role": item.source_role,
                "canonical_url": item.canonical_url,
                "fixture_label": item.fixture_label,
                "retrieval_time": item.retrieval_time.isoformat(),
                "status": item.status,
                "failure_code": item.failure_code,
                "fingerprint": item.fingerprint,
                "extractor_version": item.extractor_version,
                "offers": [
                    {
                        "item_price_minor": offer.item_price_minor,
                        "currency": offer.currency,
                        "price_toman": offer.price_toman,
                        "shipping_minor": offer.shipping_minor,
                        "mandatory_charges_minor": offer.mandatory_charges_minor,
                        "total_payable_minor": offer.total_payable_minor,
                        "seller": offer.seller,
                        "merchant_url": offer.merchant_url,
                        "observation_kind": offer.observation_kind,
                        "warranty": offer.warranty,
                        "registration": offer.registration,
                        "availability": offer.availability,
                        "observed_at": offer.observed_at.isoformat(),
                    }
                    for offer in item.offers.order_by("observed_at")
                ],
                "claims": [
                    {
                        "field": claim.field,
                        "normalized_value": claim.normalized_value,
                        "source_location": claim.source_location,
                        "evidence_status": claim.evidence_status,
                        "variant": (
                            {
                                "id": str(claim.variant_id),
                                "brand": claim.variant.product.brand,
                                "model_name": claim.variant.product.model_name,
                                "canonical_identifier": claim.variant.canonical_identifier,
                                "identifiers": claim.variant.identifiers,
                                "attributes": claim.variant.attributes,
                                "region": claim.variant.region,
                                "bundle": claim.variant.bundle,
                                "condition": claim.variant.condition,
                            }
                            if claim.variant_id else None
                        ),
                    }
                    for claim in item.claims.select_related("variant__product").order_by("created_at")
                ],
            }
            for item in snapshots
        ],
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


def owned_job(guest, job_id):
    item = ResearchJob.objects.select_related("conversation", "operation").filter(
        id=job_id,
        conversation__guest_context=guest,
        conversation__expires_at__gt=timezone.now(),
    ).first()
    if item is None:
        raise CopilotUnavailable
    return item


class ResearchStartView(CsrfProtectedAPIView):
    def post(self, request, conversation_id):
        configured_mode = settings.BEFOREBUY_RESEARCH_MODE.upper()
        if configured_mode == "OFFLINE":
            return error("RESEARCH_OFFLINE", "پژوهش عمومی در این اجرا غیرفعال است.", 409)
        if configured_mode not in {"FIXTURE", "LIVE"}:
            return error("RESEARCH_CONFIGURATION_INVALID", "پیکربندی پژوهش نامعتبر است.", 503)
        guest = get_or_create_guest(request)
        conversation = active_conversation(guest, conversation_id)
        key = request.headers.get("Idempotency-Key", "")
        expected = request.data.get("expected_brief_revision")
        raw_targets = request.data.get("targets")
        if raw_targets is None and configured_mode == "FIXTURE":
            source_ids = request.data.get("source_ids")
            raw_targets = ([{"source_id": item, "url": None} for item in source_ids]
                           if isinstance(source_ids, list) else source_ids)
        valid_targets = isinstance(raw_targets, list) and 1 <= len(raw_targets) <= 3
        targets = []
        if valid_targets:
            for item in raw_targets:
                if not isinstance(item, dict) or set(item) - {"source_id", "url"}:
                    valid_targets = False
                    break
                source_id, url = item.get("source_id"), item.get("url")
                if (not isinstance(source_id, str) or not 1 <= len(source_id) <= 253
                        or (url is not None and (not isinstance(url, str) or not 1 <= len(url) <= 1000))
                        or (configured_mode == "LIVE" and not url)):
                    valid_targets = False
                    break
                targets.append({"source_id": source_id.rstrip(".").lower(), "url": url})
        if valid_targets and len({(item["source_id"], item["url"]) for item in targets}) != len(targets):
            valid_targets = False
        if (not re.fullmatch(r"[A-Za-z0-9._:-]{16,128}", key)
                or not isinstance(expected, int) or isinstance(expected, bool) or not valid_targets):
            return error("VALIDATION_ERROR", "درخواست پژوهش نامعتبر است.", 422)
        targets = normalize_targets(targets=targets)
        request_hash = canonical_research_hash(expected, targets, configured_mode)
        if not reserve_research_slot():
            return error("RESEARCH_PROCESS_CAPACITY", "ظرفیت پژوهش موقتاً پر است.", 429)
        try:
            with transaction.atomic():
                job, replay = create_research_job(
                    conversation_id=conversation.id,
                    guest=guest,
                    expected_revision=expected,
                    idempotency_key=key,
                    request_hash=request_hash,
                    targets=targets,
                    mode=configured_mode,
                )
                if not replay:
                    transaction.on_commit(lambda job_id=job.id: submit_research_reserved(job_id))
        except ValueError as exc:
            release_research_slot()
            code = str(exc)
            status_code = 429 if code == "RESEARCH_LIMIT_REACHED" else 422 if code in {
                "SOURCE_NOT_APPROVED", "TARGET_URL_INVALID", "TARGET_SOURCE_MISMATCH"
            } else 409
            return error(code, "پذیرش اتمیک درخواست پژوهش ناموفق بود.", status_code)
        except Exception:
            release_research_slot()
            raise
        if replay:
            release_research_slot()
        job.refresh_from_db()
        job.operation.refresh_from_db()
        return Response(
            {
                "job": serialize_research_job(job),
                "operation": serialize_operation(job.operation),
                "idempotent_replay": replay,
                "events_url": f"/api/v1/operations/{job.operation_id}/events",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ResearchDetailView(CsrfProtectedAPIView):
    def get(self, request, job_id):
        job = owned_job(get_or_create_guest(request), job_id)
        return Response(serialize_research_job(reconcile_research_job(job.id)))


class ResearchCancelView(CsrfProtectedAPIView):
    def post(self, request, job_id):
        job = owned_job(get_or_create_guest(request), job_id)
        if job.operation.status in TERMINAL:
            if job.operation.status == "CANCELLED":
                return Response({"job": serialize_research_job(job), "operation": serialize_operation(job.operation)})
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        changed, operation, job = cancel_research_job(job.id)
        if not changed or operation is None:
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        return Response(
            {"job": serialize_research_job(job), "operation": serialize_operation(operation)},
            status=status.HTTP_202_ACCEPTED,
        )
