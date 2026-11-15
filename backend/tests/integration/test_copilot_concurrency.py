import threading
from datetime import timedelta
from unittest.mock import patch

from django.test import TransactionTestCase
from django.utils import timezone

from analysis.conversation.streaming import _execute, reconcile_stale_operation, reserve_execution_slot
from analysis.models import Conversation, GuestContext, Message, ShoppingBrief, StreamOperation


class CopilotConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.conversation = Conversation.objects.create_for_guest(self.guest)
        self.message = Message.objects.create(
            conversation=self.conversation, role="USER", state="ACCEPTED", text="fixture"
        )

    def operation(self):
        return StreamOperation.objects.create(
            conversation=self.conversation, user_message=self.message,
            idempotency_key=f"race-{timezone.now().timestamp()}", request_hash="a" * 64,
            expected_brief_revision=0,
        )

    def run_blocked(self, operation, mutate):
        first_chunk = threading.Event()
        release = threading.Event()

        def generated(_generator):
            first_chunk.set()
            self.assertTrue(release.wait(5), "test barrier was not released")
            yield "دلتای کنترل‌شده"

        self.assertTrue(reserve_execution_slot())
        with patch("analysis.conversation.streaming.FixtureGenerator.generate", generated):
            worker = threading.Thread(target=_execute, args=(operation.id,))
            worker.start()
            self.assertTrue(first_chunk.wait(5), "fixture worker did not reach barrier")
            mutate()
            release.set()
            worker.join(5)
            self.assertFalse(worker.is_alive(), "fixture worker did not terminate")

    def test_brief_edit_prevents_late_final_publication(self):
        operation = self.operation()

        def edit():
            ShoppingBrief.objects.filter(conversation=self.conversation).update(revision=1)
            Conversation.objects.filter(id=self.conversation.id).update(brief_revision=1)

        self.run_blocked(operation, edit)
        operation.refresh_from_db()
        self.assertEqual(operation.status, "INTERRUPTED")
        self.assertIsNone(operation.final_message_id)

    def test_explicit_cancel_wins_before_late_final_publication(self):
        operation = self.operation()
        self.run_blocked(
            operation,
            lambda: StreamOperation.objects.filter(id=operation.id).update(cancel_requested_at=timezone.now()),
        )
        operation.refresh_from_db()
        self.assertEqual(operation.status, "CANCELLED")
        self.assertIsNone(operation.final_message_id)

    def test_delete_invalidates_worker_publication(self):
        operation = self.operation()
        self.run_blocked(operation, lambda: Conversation.objects.filter(id=self.conversation.id).delete())
        self.assertFalse(StreamOperation.objects.filter(id=operation.id).exists())

    def test_stale_pending_operation_becomes_interrupted_without_restart(self):
        operation = self.operation()
        StreamOperation.objects.filter(id=operation.id).update(created_at=timezone.now() - timedelta(minutes=1))
        operation.refresh_from_db()
        reconciled = reconcile_stale_operation(operation)
        self.assertEqual(reconciled.status, "INTERRUPTED")
        self.assertEqual(reconciled.terminal_code, "WORKER_INTERRUPTED")
        self.assertIsNone(reconciled.final_message_id)
