import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from analysis.models import Conversation, GuestContext, Message, StreamOperation, UploadedImage


class OperationConflict(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


def canonical_request_hash(text, upload_ids, expected_revision):
    payload = {"text": text, "upload_ids": sorted(str(value) for value in upload_ids), "expected_brief_revision": expected_revision}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


@transaction.atomic
def accept_message(*, conversation_id, guest, text, upload_ids, expected_revision, idempotency_key):
    GuestContext.objects.select_for_update().get(id=guest.id)
    conversation = Conversation.objects.select_for_update().filter(
        id=conversation_id, guest_context=guest, expires_at__gt=timezone.now()
    ).first()
    if conversation is None:
        raise Conversation.DoesNotExist
    request_hash = canonical_request_hash(text, upload_ids, expected_revision)
    existing = StreamOperation.objects.filter(conversation=conversation, idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_hash != request_hash:
            raise OperationConflict("IDEMPOTENCY_CONFLICT", "این کلید برای درخواست دیگری استفاده شده است.")
        return existing, True
    if conversation.brief_revision != expected_revision:
        raise OperationConflict("STALE_BRIEF_REVISION", "نسخهٔ brief تغییر کرده است.")
    now = timezone.now()
    active = StreamOperation.objects.filter(conversation__guest_context=guest).filter(
        Q(status="PENDING", created_at__gt=now - timedelta(seconds=30))
        | Q(status="RUNNING", lease_expires_at__gt=now)
    ).count()
    if active >= 2:
        raise OperationConflict("OPERATION_LIMIT_REACHED", "ابتدا عملیات جاری را متوقف کنید.")
    uploads = list(UploadedImage.objects.select_for_update().filter(
        id__in=upload_ids, conversation=conversation, message__isnull=True, expires_at__gt=timezone.now()
    ))
    if len(uploads) != len(set(upload_ids)):
        raise OperationConflict("UPLOAD_UNAVAILABLE", "یک یا چند تصویر در دسترس نیست.")
    message = Message.objects.create(conversation=conversation, role="USER", state="ACCEPTED", text=text)
    UploadedImage.objects.filter(id__in=[item.id for item in uploads]).update(message=message)
    operation = StreamOperation.objects.create(
        conversation=conversation,
        user_message=message,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        expected_brief_revision=expected_revision,
    )
    expiry = now + timedelta(days=90)
    conversation.last_eligible_activity_at = now
    conversation.expires_at = expiry
    conversation.save(update_fields=["last_eligible_activity_at", "expires_at", "updated_at"])
    return operation, False
