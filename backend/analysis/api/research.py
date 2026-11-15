import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from analysis.conversation.serializers import serialize_operation
from analysis.conversation.streaming import TERMINAL, cancel_operation
from analysis.guest import get_or_create_guest
from analysis.models import Conversation, ResearchJob
from analysis.research.jobs import (
    canonical_research_hash,
    create_research_job,
    release_research_slot,
    reserve_research_slot,
    submit_research_reserved,
)

from .base import CsrfProtectedAPIView
from .conversations import active_conversation, error
from .errors import CopilotUnavailable


def serialize_research_job(job):
    snapshots = job.snapshots.order_by("created_at")
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
        "coverage": job.coverage,
        "limits": job.limits,
        "snapshots": [
            {
                "id": str(item.id),
                "source_role": item.source_role,
                "canonical_url": item.canonical_url,
                "fixture_label": item.fixture_label,
                "retrieval_time": item.retrieval_time.isoformat(),
                "status": item.status,
                "fingerprint": item.fingerprint,
                "extractor_version": item.extractor_version,
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
        source_ids = request.data.get("source_ids")
        if (
            not re.fullmatch(r"[A-Za-z0-9._:-]{16,128}", key)
            or not isinstance(expected, int)
            or not isinstance(source_ids, list)
            or not 1 <= len(source_ids) <= 3
            or len(set(source_ids)) != len(source_ids)
            or any(not isinstance(item, str) or not 1 <= len(item) <= 253 for item in source_ids)
        ):
            return error("VALIDATION_ERROR", "درخواست پژوهش نامعتبر است.", 422)
        if conversation.brief_revision != expected:
            return error(
                "STALE_BRIEF_REVISION", "نسخهٔ brief تغییر کرده است.", 409,
                current_revision=conversation.brief_revision,
            )
        if not conversation.brief.confirmed:
            return error("BRIEF_NOT_CONFIRMED", "ابتدا brief را تأیید کنید.", 409)
        request_hash = canonical_research_hash(expected, source_ids, configured_mode)
        existing = ResearchJob.objects.filter(
            conversation=conversation,
            operation__idempotency_key=key,
            operation__operation_kind="RESEARCH",
        ).select_related("operation").first()
        if existing:
            if existing.request_hash != request_hash:
                return error("IDEMPOTENCY_CONFLICT", "این کلید برای درخواست دیگری استفاده شده است.", 409)
            return Response(
                {
                    "job": serialize_research_job(existing),
                    "operation": serialize_operation(existing.operation),
                    "idempotent_replay": True,
                    "events_url": f"/api/v1/operations/{existing.operation_id}/events",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        if not reserve_research_slot():
            return error("RESEARCH_PROCESS_CAPACITY", "ظرفیت پژوهش موقتاً پر است.", 429)
        try:
            with transaction.atomic():
                job, replay = create_research_job(
                    conversation=conversation,
                    idempotency_key=key,
                    request_hash=request_hash,
                    source_ids=source_ids,
                    mode=configured_mode,
                )
                if not replay:
                    transaction.on_commit(lambda job_id=job.id: submit_research_reserved(job_id))
        except ValueError as exc:
            release_research_slot()
            code = str(exc)
            return error(code, "یک پژوهش فعال یا تعارض idempotency وجود دارد.", 429 if code == "RESEARCH_LIMIT_REACHED" else 409)
        except Exception:
            release_research_slot()
            raise
        if replay:
            release_research_slot()
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
        return Response(serialize_research_job(owned_job(get_or_create_guest(request), job_id)))


class ResearchCancelView(CsrfProtectedAPIView):
    def post(self, request, job_id):
        job = owned_job(get_or_create_guest(request), job_id)
        if job.operation.status in TERMINAL:
            if job.operation.status == "CANCELLED":
                return Response({"job": serialize_research_job(job), "operation": serialize_operation(job.operation)})
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        changed, operation = cancel_operation(job.operation_id)
        if not changed or operation is None:
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        ResearchJob.objects.filter(id=job.id).update(
            status="CANCELLED", stage="CANCELLED", terminal_code="USER_REQUEST", completed_at=timezone.now()
        )
        job.refresh_from_db()
        return Response(
            {"job": serialize_research_job(job), "operation": serialize_operation(operation)},
            status=status.HTTP_202_ACCEPTED,
        )
