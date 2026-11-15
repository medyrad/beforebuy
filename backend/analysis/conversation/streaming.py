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
LEASE_SECONDS = 30
PENDING_STALE_SECONDS = 30
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="copilot-fixture")
_capacity = threading.BoundedSemaphore(6)
_subscriber_capacity = threading.BoundedSemaphore(2)
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


def _lock_operation(operation_id):
    """Lock in the only supported order: Conversation, then StreamOperation."""
    conversation_id = StreamOperation.objects.filter(id=operation_id).values_list("conversation_id", flat=True).first()
    if conversation_id is None:
        return None, None
    conversation = Conversation.objects.select_for_update().filter(id=conversation_id).first()
    if conversation is None:
        return None, None
    operation = StreamOperation.objects.select_for_update().filter(
        id=operation_id, conversation_id=conversation.id
    ).first()
    return conversation, operation


def _create_event(operation, conversation, event_type, payload, now):
    sequence = operation.next_sequence
    body = {
        "schema_version": SCHEMA_VERSION,
        "operation_id": str(operation.id),
        "conversation_id": str(conversation.id),
        "sequence": sequence,
        "timestamp": now.isoformat(),
        **payload,
    }
    event = StreamEvent.objects.create(
        operation=operation,
        sequence=sequence,
        event_type=event_type,
        payload=body,
        expires_at=now + timedelta(hours=24),
    )
    operation.next_sequence = sequence + 1
    return event


def _terminalize_locked(operation, conversation, event_type, payload, status, code, now, *, publish=True):
    if publish:
        _create_event(operation, conversation, event_type, payload, now)
    operation.status = status
    operation.terminal_code = code
    operation.completed_at = now
    operation.lease_owner = None
    operation.lease_expires_at = None
    operation.save(update_fields=[
        "next_sequence", "status", "terminal_code", "completed_at",
        "lease_owner", "lease_expires_at", "updated_at",
    ])


@transaction.atomic
def claim_operation(operation_id, lease_owner):
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None or operation.status != "PENDING":
        return False
    if conversation.expires_at <= now:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "CONVERSATION_EXPIRED"},
            "INTERRUPTED", "CONVERSATION_EXPIRED", now, publish=False,
        )
        return False
    if conversation.brief_revision != operation.expected_brief_revision:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "STALE_BRIEF"},
            "INTERRUPTED", "STALE_BRIEF", now,
        )
        return False
    if operation.cancel_requested_at:
        _terminalize_locked(
            operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
            "CANCELLED", "USER_REQUEST", now,
        )
        return False
    operation.status = "RUNNING"
    operation.lease_owner = lease_owner
    operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    operation.started_at = now
    operation.save(update_fields=["status", "lease_owner", "lease_expires_at", "started_at", "updated_at"])
    return True


@transaction.atomic
def renew_operation_lease(operation_id, lease_owner):
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if (
        operation is None
        or conversation.expires_at <= now
        or operation.status != "RUNNING"
        or operation.lease_owner != lease_owner
        or operation.lease_expires_at is None
        or operation.lease_expires_at <= now
    ):
        return False
    operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    operation.save(update_fields=["lease_expires_at", "updated_at"])
    return True


@transaction.atomic
def _publish(operation_id, event_type, payload, *, lease_owner=None):
    """Publish a non-terminal worker event after revalidating its current lease."""
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None or operation.status != "RUNNING":
        return False
    if conversation.expires_at <= now:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "CONVERSATION_EXPIRED"},
            "INTERRUPTED", "CONVERSATION_EXPIRED", now, publish=False,
        )
        return False
    if (
        lease_owner is None
        or operation.lease_owner != lease_owner
        or operation.lease_expires_at is None
        or operation.lease_expires_at <= now
    ):
        return False
    if conversation.brief_revision != operation.expected_brief_revision:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "STALE_BRIEF"},
            "INTERRUPTED", "STALE_BRIEF", now,
        )
        return False
    if operation.cancel_requested_at:
        _terminalize_locked(
            operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
            "CANCELLED", "USER_REQUEST", now,
        )
        return False
    _create_event(operation, conversation, event_type, payload, now)
    operation.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    operation.save(update_fields=["next_sequence", "lease_expires_at", "updated_at"])
    return True


@transaction.atomic
def finalize_operation(operation_id, lease_owner, text):
    """Commit final message, final event, completion event and terminal state together."""
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None or operation.status != "RUNNING":
        return False
    if conversation.expires_at <= now:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "CONVERSATION_EXPIRED"},
            "INTERRUPTED", "CONVERSATION_EXPIRED", now, publish=False,
        )
        return False
    if (
        operation.lease_owner != lease_owner
        or operation.lease_expires_at is None
        or operation.lease_expires_at <= now
    ):
        return False
    if conversation.brief_revision != operation.expected_brief_revision:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "STALE_BRIEF"},
            "INTERRUPTED", "STALE_BRIEF", now,
        )
        return False
    if operation.cancel_requested_at:
        _terminalize_locked(
            operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
            "CANCELLED", "USER_REQUEST", now,
        )
        return False

    final = Message.objects.create(conversation=conversation, role="ASSISTANT", state="FINAL", text=text)
    _create_event(
        operation, conversation, "assistant.message.final",
        {"message_id": str(final.id), "text": text}, now,
    )
    _create_event(operation, conversation, "operation.completed", {"message_id": str(final.id)}, now)
    operation.final_message = final
    operation.status = "COMPLETED"
    operation.terminal_code = None
    operation.completed_at = now
    operation.lease_owner = None
    operation.lease_expires_at = None
    operation.save(update_fields=[
        "final_message", "next_sequence", "status", "terminal_code", "completed_at",
        "lease_owner", "lease_expires_at", "updated_at",
    ])
    return True


@transaction.atomic
def cancel_operation(operation_id):
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None:
        return False, None
    if operation.status in TERMINAL:
        return False, operation
    operation.cancel_requested_at = operation.cancel_requested_at or now
    if conversation.expires_at <= now:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "CONVERSATION_EXPIRED"},
            "INTERRUPTED", "CONVERSATION_EXPIRED", now, publish=False,
        )
    else:
        _terminalize_locked(
            operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
            "CANCELLED", "USER_REQUEST", now,
        )
    operation.save(update_fields=["cancel_requested_at", "updated_at"])
    return True, operation


@transaction.atomic
def fail_owned_operation(operation_id, lease_owner, code):
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if (
        operation is None
        or operation.status != "RUNNING"
        or operation.lease_owner != lease_owner
        or operation.lease_expires_at is None
        or operation.lease_expires_at <= now
    ):
        return False
    publish = conversation.expires_at > now
    _terminalize_locked(
        operation, conversation, "operation.failed", {"code": code},
        "FAILED", code, now, publish=publish,
    )
    return True


@transaction.atomic
def fail_unstarted_operation(operation_id, code="SUBMISSION_FAILED"):
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None or operation.status != "PENDING":
        return False
    publish = conversation.expires_at > now
    _terminalize_locked(
        operation, conversation, "operation.failed", {"code": code},
        "FAILED", code, now, publish=publish,
    )
    return True


def _execute(operation_id):
    close_old_connections()
    try:
        if not claim_operation(operation_id, _worker_identity):
            return
        if not _publish(
            operation_id, "operation.started", {"kind": "DEVELOPMENT_FIXTURE"},
            lease_owner=_worker_identity,
        ):
            return
        text = ""
        for chunk in FixtureGenerator().generate():
            time.sleep(0.12)
            if len(chunk.encode("utf-8")) > 1024:
                raise ValueError("fixture delta exceeds contract")
            if not _publish(
                operation_id, "assistant.text.delta", {"text": chunk},
                lease_owner=_worker_identity,
            ):
                return
            text += chunk
        finalize_operation(operation_id, _worker_identity, text)
    except Exception:
        fail_owned_operation(operation_id, _worker_identity, "FIXTURE_FAILED")
    finally:
        close_old_connections()
        _capacity.release()


def reserve_execution_slot():
    return _capacity.acquire(blocking=False)


def release_execution_slot():
    _capacity.release()


def submit_reserved(operation_id):
    try:
        _executor.submit(_execute, operation_id)
    except Exception:
        try:
            fail_unstarted_operation(operation_id)
        finally:
            release_execution_slot()
        return False
    return True


def reserve_subscriber_slot():
    return _subscriber_capacity.acquire(blocking=False)


def release_subscriber_slot():
    _subscriber_capacity.release()


@transaction.atomic
def reconcile_stale_operation(operation_or_id):
    operation_id = getattr(operation_or_id, "id", operation_or_id)
    now = timezone.now()
    conversation, operation = _lock_operation(operation_id)
    if operation is None:
        return None
    if operation.status in TERMINAL:
        return operation
    if conversation.expires_at <= now:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "CONVERSATION_EXPIRED"},
            "INTERRUPTED", "CONVERSATION_EXPIRED", now, publish=False,
        )
        return operation
    if conversation.brief_revision != operation.expected_brief_revision:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "STALE_BRIEF"},
            "INTERRUPTED", "STALE_BRIEF", now,
        )
        return operation
    if operation.cancel_requested_at:
        _terminalize_locked(
            operation, conversation, "operation.cancelled", {"reason": "USER_REQUEST"},
            "CANCELLED", "USER_REQUEST", now,
        )
        return operation
    pending_stale = (
        operation.status == "PENDING"
        and operation.created_at <= now - timedelta(seconds=PENDING_STALE_SECONDS)
    )
    running_stale = (
        operation.status == "RUNNING"
        and (operation.lease_expires_at is None or operation.lease_expires_at <= now)
    )
    if pending_stale or running_stale:
        _terminalize_locked(
            operation, conversation, "operation.failed", {"code": "WORKER_INTERRUPTED"},
            "INTERRUPTED", "WORKER_INTERRUPTED", now,
        )
    return operation


def encode_event(event):
    return (
        f"id: {event.operation_id}:{event.sequence}\n"
        f"event: {event.event_type}\n"
        f"data: {json.dumps(event.payload, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )


def encode_replay_gap(operation_id):
    payload = json.dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "operation_id": str(operation_id),
            "code": "REPLAY_GAP",
            "reconcile_url": f"/api/v1/operations/{operation_id}",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"event: stream.replay_gap\ndata: {payload}\n\n"
