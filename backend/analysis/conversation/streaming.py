import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.db import close_old_connections, transaction
from django.utils import timezone

from analysis.models import Conversation, Message, StreamEvent, StreamOperation


SCHEMA_VERSION = "COPILOT-STREAM-v1"
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="copilot-fixture")
_capacity = threading.BoundedSemaphore(6)
_worker_identity = f"{os.getpid()}-{id(_executor):x}"


class FixtureGenerator:
    """Honest deterministic development generator; it performs no network or NLP inference."""

    chunks = (
        "پیام شما ثبت شد. ",
        "این پاسخ فقط fixture توسعه است و متن آزاد را تفسیر نمی‌کند. ",
        "برای ادامه، اطلاعات قطعی مانند بودجه، مخاطب و کاربرد را در brief ویرایش و تأیید کنید.",
    )

    def generate(self):
        yield from self.chunks


def _publish(operation_id, event_type, payload, *, terminal_status=None, terminal_code=None):
    with transaction.atomic():
        operation = StreamOperation.objects.select_for_update().select_related("conversation").filter(id=operation_id).first()
        if operation is None or operation.status not in ({"RUNNING"} if terminal_status is None else {"RUNNING", "PENDING"}):
            return False
        conversation = operation.conversation
        if conversation.brief_revision != operation.expected_brief_revision:
            terminal_status, terminal_code = "INTERRUPTED", "STALE_BRIEF"
            event_type, payload = "operation.failed", {"code": terminal_code}
        sequence = operation.next_sequence
        now = timezone.now()
        body = {
            "schema_version": SCHEMA_VERSION,
            "operation_id": str(operation.id),
            "conversation_id": str(conversation.id),
            "sequence": sequence,
            "timestamp": now.isoformat(),
            **payload,
        }
        StreamEvent.objects.create(
            operation=operation, sequence=sequence, event_type=event_type, payload=body,
            expires_at=now + timedelta(hours=24),
        )
        operation.next_sequence = sequence + 1
        fields = ["next_sequence", "updated_at"]
        if terminal_status:
            operation.status = terminal_status
            operation.terminal_code = terminal_code
            operation.completed_at = now
            fields += ["status", "terminal_code", "completed_at"]
        operation.save(update_fields=fields)
        return terminal_status not in {"INTERRUPTED", "CANCELLED"}


def _execute(operation_id):
    close_old_connections()
    try:
        now = timezone.now()
        claimed = StreamOperation.objects.filter(id=operation_id, status="PENDING").update(
            status="RUNNING", lease_owner=_worker_identity, lease_expires_at=now + timedelta(seconds=30), started_at=now
        )
        if not claimed:
            return
        if not _publish(operation_id, "operation.started", {"kind": "DEVELOPMENT_FIXTURE"}):
            return
        text = ""
        for chunk in FixtureGenerator().generate():
            time.sleep(0.12)
            operation = StreamOperation.objects.filter(id=operation_id).only("status", "cancel_requested_at").first()
            if operation is None:
                return
            if operation.cancel_requested_at or operation.status == "CANCELLED":
                _publish(operation_id, "operation.cancelled", {"reason": "USER_REQUEST"}, terminal_status="CANCELLED", terminal_code="USER_REQUEST")
                return
            if len(chunk.encode("utf-8")) > 1024:
                raise ValueError("fixture delta exceeds contract")
            if not _publish(operation_id, "assistant.text.delta", {"text": chunk}):
                return
            text += chunk
        with transaction.atomic():
            operation = StreamOperation.objects.select_for_update().select_related("conversation").filter(id=operation_id, status="RUNNING").first()
            if operation is None or operation.cancel_requested_at:
                return
            if operation.conversation.brief_revision != operation.expected_brief_revision:
                _publish(operation_id, "operation.failed", {"code": "STALE_BRIEF"}, terminal_status="INTERRUPTED", terminal_code="STALE_BRIEF")
                return
            final = Message.objects.create(conversation=operation.conversation, role="ASSISTANT", state="FINAL", text=text)
            operation.final_message = final
            operation.save(update_fields=["final_message", "updated_at"])
        _publish(operation_id, "assistant.message.final", {"message_id": str(final.id), "text": text})
        _publish(operation_id, "operation.completed", {"message_id": str(final.id)}, terminal_status="COMPLETED")
    except Exception:
        _publish(operation_id, "operation.failed", {"code": "FIXTURE_FAILED"}, terminal_status="FAILED", terminal_code="FIXTURE_FAILED")
    finally:
        close_old_connections()
        _capacity.release()


def reserve_execution_slot():
    return _capacity.acquire(blocking=False)


def release_execution_slot():
    _capacity.release()


def submit_reserved(operation_id):
    _executor.submit(_execute, operation_id)


def reconcile_stale_operation(operation):
    now = timezone.now()
    pending_stale = operation.status == "PENDING" and operation.created_at <= now - timedelta(seconds=30)
    running_stale = operation.status == "RUNNING" and operation.lease_expires_at and operation.lease_expires_at <= now
    if pending_stale or running_stale:
        _publish(operation.id, "operation.failed", {"code": "WORKER_INTERRUPTED"}, terminal_status="INTERRUPTED", terminal_code="WORKER_INTERRUPTED")
        operation.refresh_from_db()
    return operation


def encode_event(event):
    return f"id: {event.operation_id}:{event.sequence}\nevent: {event.event_type}\ndata: {json.dumps(event.payload, ensure_ascii=False, separators=(',', ':'))}\n\n"
