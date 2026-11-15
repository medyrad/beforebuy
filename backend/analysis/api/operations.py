import re
import threading
import time
from datetime import timedelta

from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.renderers import BaseRenderer, JSONRenderer

from analysis.conversation.serializers import serialize_operation
from analysis.conversation.streaming import (
    TERMINAL,
    cancel_operation,
    encode_event,
    encode_replay_gap,
    reconcile_stale_operation,
    release_subscriber_slot,
    reserve_subscriber_slot,
)
from analysis.guest import get_or_create_guest
from analysis.models import StreamEvent, StreamOperation

from .base import CsrfProtectedAPIView
from .conversations import error
from .errors import CopilotUnavailable


STREAM_LIFETIME_SECONDS = 45
HEARTBEAT_SECONDS = 15
POLL_SECONDS = 0.08


def stream_error(code, message, status_code, **extra):
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status_code)


class ClosingIterator:
    """Ensure capacity is released even when a response closes before first iteration."""

    def __init__(self, iterator, closer):
        self.iterator = iterator
        self.closer = closer

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)

    def close(self):
        try:
            self.iterator.close()
        finally:
            self.closer()


def owned_operation(guest, operation_id):
    query = StreamOperation.objects.select_related("conversation").filter(
        id=operation_id, conversation__guest_context=guest, conversation__expires_at__gt=timezone.now()
    )
    operation = query.first()
    if operation is None:
        raise CopilotUnavailable
    return operation


class OperationDetailView(CsrfProtectedAPIView):
    def get(self, request, operation_id):
        operation = reconcile_stale_operation(owned_operation(get_or_create_guest(request), operation_id))
        return Response(serialize_operation(operation))


class OperationCancelView(CsrfProtectedAPIView):
    def post(self, request, operation_id):
        operation = owned_operation(get_or_create_guest(request), operation_id)
        if operation.status == "CANCELLED":
            return Response(serialize_operation(operation))
        if operation.status in TERMINAL:
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        changed, operation = cancel_operation(operation.id)
        if operation is None:
            raise CopilotUnavailable
        if not changed:
            if operation.status == "CANCELLED":
                return Response(serialize_operation(operation))
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        return Response(serialize_operation(operation), status=202)


class EventStreamRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "sse"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # StreamingHttpResponse bypasses this; this safe JSON form is only for pre-stream errors.
        import json
        return json.dumps(data, ensure_ascii=False).encode("utf-8")


class OperationEventView(CsrfProtectedAPIView):
    renderer_classes = [EventStreamRenderer, JSONRenderer]

    def get(self, request, operation_id):
        operation = reconcile_stale_operation(owned_operation(get_or_create_guest(request), operation_id))
        if operation is None:
            raise CopilotUnavailable
        after = 0
        raw = request.headers.get("Last-Event-ID")
        if raw:
            match = re.fullmatch(r"([0-9a-fA-F-]{36}):(\d+)", raw)
            if not match or match.group(1).lower() != str(operation.id).lower():
                return stream_error("INVALID_REPLAY_ID", "شناسهٔ replay نامعتبر است.", 400)
            after = int(match.group(2))
        highest = operation.next_sequence - 1
        if after > highest:
            return stream_error(
                "INVALID_REPLAY_SEQUENCE", "sequence در آینده یا ناموجود است؛ وضعیت REST را بخوانید.", 409,
                reconcile_url=f"/api/v1/operations/{operation.id}",
            )
        retained = StreamEvent.objects.filter(operation=operation, expires_at__gt=timezone.now())
        first = retained.filter(sequence__gt=after).order_by("sequence").values_list("sequence", flat=True).first()
        if after < highest and first != after + 1:
            return stream_error(
                "REPLAY_GAP", "رویدادهای لازم دیگر نگه‌داری نمی‌شوند؛ وضعیت REST را بخوانید.", 409,
                reconcile_url=f"/api/v1/operations/{operation.id}",
            )

        if not reserve_subscriber_slot():
            return stream_error("STREAM_CAPACITY_REACHED", "ظرفیت stream موقتاً پر است.", 429)

        release_lock = threading.Lock()
        released = False

        def release_once():
            nonlocal released
            with release_lock:
                if not released:
                    released = True
                    release_subscriber_slot()

        def stream():
            sequence = after
            started = time.monotonic()
            last_heartbeat = started
            try:
                while time.monotonic() - started < STREAM_LIFETIME_SECONDS:
                    now = timezone.now()
                    state = StreamOperation.objects.filter(id=operation.id).values(
                        "status", "next_sequence", "created_at", "lease_expires_at",
                        "conversation__expires_at",
                    ).first()
                    if state is None:
                        return
                    if state["conversation__expires_at"] <= now:
                        reconcile_stale_operation(operation.id)
                        return
                    apparently_stale = (
                        state["status"] == "PENDING"
                        and state["created_at"] <= now - timedelta(seconds=30)
                    ) or (
                        state["status"] == "RUNNING"
                        and (state["lease_expires_at"] is None or state["lease_expires_at"] <= now)
                    )
                    if apparently_stale:
                        current = reconcile_stale_operation(operation.id)
                        if current is None:
                            return
                        state["status"] = current.status
                        state["next_sequence"] = current.next_sequence

                    highest_now = state["next_sequence"] - 1
                    events = list(StreamEvent.objects.filter(
                        operation_id=operation.id,
                        sequence__gt=sequence,
                        expires_at__gt=now,
                    ).order_by("sequence")[:100])
                    if sequence < highest_now and (not events or events[0].sequence != sequence + 1):
                        yield encode_replay_gap(operation.id).encode("utf-8")
                        return
                    for event in events:
                        if event.sequence != sequence + 1:
                            yield encode_replay_gap(operation.id).encode("utf-8")
                            return
                        if not StreamEvent.objects.filter(
                            id=event.id, expires_at__gt=timezone.now()
                        ).exists():
                            yield encode_replay_gap(operation.id).encode("utf-8")
                            return
                        sequence = event.sequence
                        yield encode_event(event).encode("utf-8")
                    if state["status"] in TERMINAL and sequence >= highest_now:
                        return
                    if time.monotonic() - last_heartbeat >= HEARTBEAT_SECONDS:
                        yield b": heartbeat\n\n"
                        last_heartbeat = time.monotonic()
                    time.sleep(POLL_SECONDS)
            finally:
                release_once()

        iterator = ClosingIterator(stream(), release_once)
        response = StreamingHttpResponse(iterator, content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
