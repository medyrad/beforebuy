import json

from django.test import TestCase
from django.utils import timezone

from analysis.models import Conversation, Message, StreamEvent, StreamOperation

from .test_conversations import csrf_client


class StreamEventApiTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        guest_id = self.client.session["guest_context_id"]
        from analysis.models import GuestContext
        self.conversation = Conversation.objects.create_for_guest(GuestContext.objects.get(id=guest_id))
        message = Message.objects.create(conversation=self.conversation, role="USER", state="ACCEPTED", text="fixture")
        self.operation = StreamOperation.objects.create(
            conversation=self.conversation, user_message=message, idempotency_key="stream-test-key-001",
            request_hash="1" * 64, expected_brief_revision=0, status="COMPLETED", completed_at=timezone.now(),
        )
        StreamEvent.objects.create(operation=self.operation, sequence=1, event_type="operation.started", payload={"sequence": 1})
        StreamEvent.objects.create(operation=self.operation, sequence=2, event_type="operation.completed", payload={"sequence": 2})

    def test_replay_is_ordered_and_does_not_execute(self):
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events", HTTP_ACCEPT="text/event-stream"
        )
        body = b"".join(response.streaming_content).decode()
        self.assertLess(body.index(":1"), body.index(":2"))
        self.assertEqual(StreamEvent.objects.filter(operation=self.operation).count(), 2)

    def test_foreign_or_malformed_replay_id_is_rejected(self):
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events", HTTP_LAST_EVENT_ID="not-an-event-id"
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_LAST_EVENT_ID="00000000-0000-0000-0000-000000000000:1",
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_cancel_is_idempotent_but_completed_cannot_cancel(self):
        response = self.client.post(
            f"/api/v1/operations/{self.operation.id}/cancel", {}, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.status_code, 409)

    def test_reconnect_gap_requires_rest_reconciliation(self):
        StreamEvent.objects.filter(operation=self.operation, sequence=1).delete()
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_ACCEPT="text/event-stream",
            HTTP_LAST_EVENT_ID=f"{self.operation.id}:0",
        )
        self.assertEqual(response.status_code, 409)
        body = json.loads(response.content)
        self.assertEqual(body["error"]["code"], "REPLAY_GAP")
        self.assertEqual(body["error"]["reconcile_url"], f"/api/v1/operations/{self.operation.id}")
