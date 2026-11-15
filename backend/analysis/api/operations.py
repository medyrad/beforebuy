import re
import time

from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.renderers import BaseRenderer, JSONRenderer

from analysis.conversation.serializers import serialize_operation
from analysis.conversation.streaming import TERMINAL, _publish, encode_event, reconcile_stale_operation
from analysis.guest import get_or_create_guest
from analysis.models import StreamEvent, StreamOperation

from .base import CsrfProtectedAPIView
from .conversations import error
from .errors import CopilotUnavailable


def owned_operation(guest, operation_id, *, lock=False):
    query = StreamOperation.objects.select_related("conversation").filter(
        id=operation_id, conversation__guest_context=guest, conversation__expires_at__gt=timezone.now()
    )
    if lock:
        query = query.select_for_update()
    operation = query.first()
    if operation is None:
        raise CopilotUnavailable
    return operation


class OperationDetailView(CsrfProtectedAPIView):
    def get(self, request, operation_id):
        operation = reconcile_stale_operation(owned_operation(get_or_create_guest(request), operation_id))
        return Response(serialize_operation(operation))


class OperationCancelView(CsrfProtectedAPIView):
    @transaction.atomic
    def post(self, request, operation_id):
        operation = owned_operation(get_or_create_guest(request), operation_id, lock=True)
        if operation.status == "CANCELLED":
            return Response(serialize_operation(operation))
        if operation.status in TERMINAL:
            return error("OPERATION_TERMINAL", "عملیات پایان یافته است.", 409)
        if operation.cancel_requested_at:
            return Response(serialize_operation(operation))
        operation.cancel_requested_at = timezone.now()
        operation.save(update_fields=["cancel_requested_at", "updated_at"])
        if operation.status == "PENDING":
            transaction.on_commit(lambda: _publish(
                operation.id, "operation.cancelled", {"reason": "USER_REQUEST"},
                terminal_status="CANCELLED", terminal_code="USER_REQUEST",
            ))
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
        operation = owned_operation(get_or_create_guest(request), operation_id)
        after = 0
        raw = request.headers.get("Last-Event-ID")
        if raw:
            match = re.fullmatch(r"([0-9a-fA-F-]{36}):(\d+)", raw)
            if not match or match.group(1).lower() != str(operation.id).lower():
                return error("INVALID_REPLAY_ID", "شناسهٔ replay نامعتبر است.", 400)
            after = int(match.group(2))
        retained = StreamEvent.objects.filter(operation=operation, expires_at__gt=timezone.now())
        first = retained.order_by("sequence").values_list("sequence", flat=True).first()
        if first is not None and raw is not None and after < first - 1:
            return error(
                "REPLAY_GAP", "رویدادهای لازم دیگر نگه‌داری نمی‌شوند؛ وضعیت REST را بخوانید.", 409,
                reconcile_url=f"/api/v1/operations/{operation.id}",
            )

        def stream():
            sequence = after
            last_heartbeat = time.monotonic()
            while True:
                events = list(StreamEvent.objects.filter(
                    operation_id=operation.id, sequence__gt=sequence, expires_at__gt=timezone.now()
                ).order_by("sequence")[:100])
                for event in events:
                    sequence = event.sequence
                    yield encode_event(event).encode("utf-8")
                current = StreamOperation.objects.filter(id=operation.id).values_list("status", flat=True).first()
                if current is None or (current in TERMINAL and not events):
                    return
                if time.monotonic() - last_heartbeat >= 15:
                    yield b": heartbeat\n\n"
                    last_heartbeat = time.monotonic()
                time.sleep(0.08)

        response = StreamingHttpResponse(stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
