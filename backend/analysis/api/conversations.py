import base64
import re
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from analysis.conversation.brief import validate_brief_changes
from analysis.conversation.operations import OperationConflict, accept_message, canonical_request_hash
from analysis.conversation.serializers import serialize_brief, serialize_conversation, serialize_operation
from analysis.conversation.streaming import release_execution_slot, reserve_execution_slot, submit_reserved
from analysis.guest import extend_guest_session_for_eligible_action, get_or_create_guest
from analysis.models import Conversation, ShoppingBrief, StreamOperation

from .base import CsrfProtectedAPIView
from .errors import CopilotUnavailable


def active_conversation(guest, conversation_id, *, lock=False):
    query = Conversation.objects.filter(
        id=conversation_id, guest_context=guest, expires_at__gt=timezone.now()
    )
    if lock:
        query = query.select_for_update()
    else:
        query = query.select_related("brief")
    item = query.first()
    if item is None:
        raise CopilotUnavailable
    return item


def error(code, message, status_code, **extra):
    return Response({"error": {"code": code, "message": message, **extra}}, status=status_code)


class ConversationListCreateView(CsrfProtectedAPIView):
    def get(self, request):
        guest = get_or_create_guest(request)
        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 20))))
            cursor = request.query_params.get("cursor")
            offset = int(base64.urlsafe_b64decode(cursor.encode()).decode()) if cursor else 0
            if offset < 0:
                raise ValueError
        except (ValueError, TypeError):
            return error("INVALID_CURSOR", "cursor یا limit نامعتبر است.", 400)
        query = Conversation.objects.filter(guest_context=guest, expires_at__gt=timezone.now()).order_by("-updated_at", "-id")
        items = list(query[offset:offset + limit + 1])
        next_cursor = None
        if len(items) > limit:
            items.pop()
            next_cursor = base64.urlsafe_b64encode(str(offset + limit).encode()).decode()
        return Response({"items": [serialize_conversation(item) for item in items], "next_cursor": next_cursor})

    def post(self, request):
        guest = get_or_create_guest(request)
        title = str(request.data.get("title", "گفت‌وگوی خرید")).strip()
        temporary = request.data.get("temporary", False)
        if type(temporary) is not bool:
            return error("VALIDATION_ERROR", "حالت بدون حافظه نامعتبر است.", 422)
        if not title or len(title) > 120:
            return error("VALIDATION_ERROR", "عنوان باید ۱ تا ۱۲۰ نویسه باشد.", 422)
        item = Conversation.objects.create_for_guest(guest, title=title)
        item.temporary = temporary
        item.save(update_fields=["temporary"])
        return Response(serialize_conversation(item, detail=True), status=status.HTTP_201_CREATED)


class ConversationDetailView(CsrfProtectedAPIView):
    def get(self, request, conversation_id):
        guest = get_or_create_guest(request)
        return Response(serialize_conversation(active_conversation(guest, conversation_id), detail=True))

    @transaction.atomic
    def delete(self, request, conversation_id):
        guest = get_or_create_guest(request)
        item = active_conversation(guest, conversation_id, lock=True)
        item.generation_epoch += 1
        item.save(update_fields=["generation_epoch", "updated_at"])
        StreamOperation.objects.filter(conversation=item, status__in=["PENDING", "RUNNING"]).update(
            cancel_requested_at=timezone.now()
        )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BriefView(CsrfProtectedAPIView):
    def get(self, request, conversation_id):
        guest = get_or_create_guest(request)
        return Response(serialize_brief(active_conversation(guest, conversation_id).brief))

    @transaction.atomic
    def patch(self, request, conversation_id):
        guest = get_or_create_guest(request)
        conversation = active_conversation(guest, conversation_id, lock=True)
        expected = request.data.get("expected_revision")
        if expected != conversation.brief_revision:
            return error("STALE_BRIEF_REVISION", "نسخهٔ brief تغییر کرده است.", 409, current_revision=conversation.brief_revision)
        try:
            changes = validate_brief_changes(request.data.get("changes"))
        except ValidationError as exc:
            return error("VALIDATION_ERROR", "تغییرهای brief نامعتبر است.", 422, field_errors=exc.detail)
        brief = ShoppingBrief.objects.select_for_update().get(conversation=conversation)
        for key, value in changes.items():
            setattr(brief, key, value)
        if "unknowns" not in changes:
            standard = {
                "مخاطب خرید": brief.recipient_context is None,
                "دستهٔ محصول": brief.category is None,
                "بودجه": brief.budget_toman is None,
                "کاربرد اصلی": not brief.use_cases,
            }
            custom = [item for item in brief.unknowns if item not in standard]
            brief.unknowns = [*custom, *[label for label, missing in standard.items() if missing]]
        brief.revision += 1
        brief.confirmed = False
        edit_id = str(uuid.uuid4())
        brief.provenance = [
            *brief.provenance,
            *[
                {"field": key, "source_type": "EXPLICIT_EDIT", "source_id": edit_id}
                for key in changes
            ],
        ]
        brief.save()
        now = timezone.now()
        conversation.brief_revision = brief.revision
        conversation.generation_epoch += 1
        conversation.last_eligible_activity_at = now
        conversation.expires_at = now + timedelta(days=90)
        conversation.save(update_fields=["brief_revision", "generation_epoch", "last_eligible_activity_at", "expires_at", "updated_at"])
        StreamOperation.objects.filter(conversation=conversation, status__in=["PENDING", "RUNNING"]).update(cancel_requested_at=now)
        extend_guest_session_for_eligible_action(request, conversation.expires_at)
        return Response(serialize_brief(brief))


class BriefConfirmView(CsrfProtectedAPIView):
    @transaction.atomic
    def post(self, request, conversation_id):
        guest = get_or_create_guest(request)
        conversation = active_conversation(guest, conversation_id, lock=True)
        if request.data.get("expected_revision") != conversation.brief_revision:
            return error("STALE_BRIEF_REVISION", "نسخهٔ brief تغییر کرده است.", 409, current_revision=conversation.brief_revision)
        brief = ShoppingBrief.objects.select_for_update().get(conversation=conversation)
        brief.confirmed = True
        brief.save(update_fields=["confirmed", "updated_at"])
        now = timezone.now()
        conversation.last_eligible_activity_at = now
        conversation.expires_at = now + timedelta(days=90)
        conversation.save(update_fields=["last_eligible_activity_at", "expires_at", "updated_at"])
        extend_guest_session_for_eligible_action(request, conversation.expires_at)
        return Response(serialize_brief(brief))


class MessageSubmitView(CsrfProtectedAPIView):
    def post(self, request, conversation_id):
        guest = get_or_create_guest(request)
        key = request.headers.get("Idempotency-Key", "")
        text = str(request.data.get("text", "")).strip()
        upload_ids = request.data.get("upload_ids", [])
        expected = request.data.get("expected_brief_revision")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{16,128}", key) or not text or len(text) > 8000 or not isinstance(upload_ids, list) or len(upload_ids) > 3 or not isinstance(expected, int):
            return error("VALIDATION_ERROR", "پیام، کلید idempotency یا revision نامعتبر است.", 422)
        try:
            upload_ids = [uuid.UUID(str(value)) for value in upload_ids]
        except (ValueError, TypeError, AttributeError):
            return error("VALIDATION_ERROR", "شناسهٔ تصویر نامعتبر است.", 422)
        conversation = active_conversation(guest, conversation_id)
        existing = StreamOperation.objects.filter(conversation=conversation, idempotency_key=key).first()
        if existing:
            request_hash = canonical_request_hash(text, upload_ids, expected)
            if existing.request_hash != request_hash:
                return error("IDEMPOTENCY_CONFLICT", "این کلید برای درخواست دیگری استفاده شده است.", 409)
            return Response({
                "operation": serialize_operation(existing),
                "message_id": str(existing.user_message_id),
                "idempotent_replay": True,
                "events_url": f"/api/v1/operations/{existing.id}/events",
            }, status=status.HTTP_202_ACCEPTED)
        if not reserve_execution_slot():
            return error("PROCESS_CAPACITY_REACHED", "ظرفیت fixture موقتاً پر است.", 429)
        try:
            with transaction.atomic():
                operation, replay = accept_message(
                    conversation_id=conversation_id, guest=guest, text=text, upload_ids=upload_ids,
                    expected_revision=expected, idempotency_key=key,
                )
                if not replay:
                    transaction.on_commit(lambda operation_id=operation.id: submit_reserved(operation_id))
        except Conversation.DoesNotExist:
            release_execution_slot()
            raise CopilotUnavailable
        except OperationConflict as exc:
            release_execution_slot()
            code = 429 if exc.code == "OPERATION_LIMIT_REACHED" else 409
            return error(exc.code, exc.message, code)
        except Exception:
            release_execution_slot()
            raise
        if replay:
            release_execution_slot()
        else:
            operation.refresh_from_db()
            extend_guest_session_for_eligible_action(request, operation.conversation.expires_at)
        return Response({
            "operation": serialize_operation(operation),
            "message_id": str(operation.user_message_id),
            "idempotent_replay": replay,
            "events_url": f"/api/v1/operations/{operation.id}/events",
        }, status=status.HTTP_202_ACCEPTED)
