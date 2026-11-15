import json
from datetime import timedelta
from unittest.mock import patch

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
        StreamOperation.objects.filter(id=self.operation.id).update(next_sequence=3)
        self.operation.refresh_from_db()

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

    def test_entire_history_expired_requires_rest_reconciliation(self):
        StreamEvent.objects.filter(operation=self.operation).update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_ACCEPT="text/event-stream", HTTP_LAST_EVENT_ID=f"{self.operation.id}:0",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "REPLAY_GAP")

    def test_future_sequence_is_rejected_but_latest_terminal_sequence_closes(self):
        future = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_ACCEPT="text/event-stream", HTTP_LAST_EVENT_ID=f"{self.operation.id}:3",
        )
        self.assertEqual(future.status_code, 409)
        self.assertEqual(future.json()["error"]["code"], "INVALID_REPLAY_SEQUENCE")
        latest = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_ACCEPT="text/event-stream", HTTP_LAST_EVENT_ID=f"{self.operation.id}:2",
        )
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(b"".join(latest.streaming_content), b"")

    def test_no_history_operation_is_not_misclassified_as_gap(self):
        empty = StreamOperation.objects.create(
            conversation=self.conversation,
            user_message=Message.objects.create(
                conversation=self.conversation, role="USER", state="ACCEPTED", text="empty"
            ),
            idempotency_key="stream-empty-key-001", request_hash="2" * 64,
            expected_brief_revision=0, status="COMPLETED", completed_at=timezone.now(),
        )
        response = self.client.get(
            f"/api/v1/operations/{empty.id}/events", HTTP_ACCEPT="text/event-stream"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"")

    @patch("analysis.api.operations.release_subscriber_slot")
    @patch("analysis.api.operations.reserve_subscriber_slot", side_effect=[True, True, False])
    def test_subscriber_admission_rejects_third_connection(self, _reserve, _release):
        first = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        second = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        third = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertEqual(third.json()["error"]["code"], "STREAM_CAPACITY_REACHED")

    def test_worker_disappears_while_subscriber_is_connected(self):
        StreamEvent.objects.filter(operation=self.operation).delete()
        StreamOperation.objects.filter(id=self.operation.id).update(
            status="RUNNING", completed_at=None, next_sequence=1,
            lease_owner="lost-worker", lease_expires_at=timezone.now() + timedelta(minutes=1),
        )
        response = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        StreamOperation.objects.filter(id=self.operation.id).update(
            lease_expires_at=timezone.now() - timedelta(seconds=1)
        )
        body = b"".join(response.streaming_content).decode()
        self.assertIn("operation.failed", body)
        self.operation.refresh_from_db()
        self.assertEqual(self.operation.status, "INTERRUPTED")

    def test_conversation_expiry_during_stream_closes_without_post_expiry_event(self):
        StreamEvent.objects.filter(operation=self.operation).delete()
        StreamOperation.objects.filter(id=self.operation.id).update(
            status="RUNNING", completed_at=None, next_sequence=1,
            lease_owner="worker", lease_expires_at=timezone.now() + timedelta(minutes=1),
        )
        response = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        Conversation.objects.filter(id=self.conversation.id).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(b"".join(response.streaming_content), b"")
        self.operation.refresh_from_db()
        self.assertEqual(self.operation.status, "INTERRUPTED")
        self.assertEqual(self.operation.terminal_code, "CONVERSATION_EXPIRED")
        self.assertFalse(StreamEvent.objects.filter(operation=self.operation).exists())

    def test_purge_race_after_stream_start_emits_control_gap(self):
        StreamEvent.objects.filter(operation=self.operation, sequence=2).delete()
        StreamOperation.objects.filter(id=self.operation.id).update(
            status="RUNNING", completed_at=None, next_sequence=2,
            lease_owner="worker", lease_expires_at=timezone.now() + timedelta(minutes=1),
        )
        response = self.client.get(
            f"/api/v1/operations/{self.operation.id}/events",
            HTTP_LAST_EVENT_ID=f"{self.operation.id}:1",
        )
        event = StreamEvent.objects.create(
            operation=self.operation, sequence=2, event_type="assistant.text.delta",
            payload={"sequence": 2}, expires_at=timezone.now() - timedelta(seconds=1),
        )
        StreamOperation.objects.filter(id=self.operation.id).update(next_sequence=3)
        body = next(iter(response.streaming_content)).decode()
        self.assertIn("event: stream.replay_gap", body)
        self.assertIn(f"/api/v1/operations/{self.operation.id}", body)
        b"".join(response.streaming_content)
        event.delete()

    def test_two_live_subscribers_leave_status_and_cancel_serviceable(self):
        StreamEvent.objects.filter(operation=self.operation).delete()
        StreamOperation.objects.filter(id=self.operation.id).update(
            status="RUNNING", completed_at=None, next_sequence=1,
            lease_owner="worker", lease_expires_at=timezone.now() + timedelta(minutes=1),
        )
        first = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        second = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        self.assertEqual(self.client.get(f"/api/v1/operations/{self.operation.id}").status_code, 200)
        cancelled = self.client.post(
            f"/api/v1/operations/{self.operation.id}/cancel", {}, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(cancelled.status_code, 202)
        self.assertEqual(cancelled.json()["status"], "CANCELLED")
        self.assertIn(b"operation.cancelled", b"".join(first.streaming_content))
        self.assertIn(b"operation.cancelled", b"".join(second.streaming_content))

    @patch("analysis.api.operations.STREAM_LIFETIME_SECONDS", 0)
    def test_connection_lifetime_is_bounded_and_releases_admission(self):
        StreamEvent.objects.filter(operation=self.operation).delete()
        StreamOperation.objects.filter(id=self.operation.id).update(
            status="RUNNING", completed_at=None, next_sequence=1,
            lease_owner="worker", lease_expires_at=timezone.now() + timedelta(minutes=1),
        )
        response = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        self.assertEqual(b"".join(response.streaming_content), b"")
        again = self.client.get(f"/api/v1/operations/{self.operation.id}/events")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(b"".join(again.streaming_content), b"")
