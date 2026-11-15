import threading
from datetime import timedelta
from unittest.mock import patch

from django.test import Client
from django.test import TransactionTestCase
from django.utils import timezone

from analysis.conversation.streaming import (
    _execute,
    claim_operation,
    finalize_operation,
    reconcile_stale_operation,
    renew_operation_lease,
    reserve_execution_slot,
)
from analysis.conversation import streaming
from analysis.models import Conversation, GuestContext, Message, ShoppingBrief, StreamEvent, StreamOperation


class CopilotConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.conversation = Conversation.objects.create_for_guest(self.guest)
        self.message = Message.objects.create(
            conversation=self.conversation, role="USER", state="ACCEPTED", text="fixture"
        )
        self.client = Client()
        session = self.client.session
        session["guest_context_id"] = str(self.guest.id)
        session.save()

    def operation(self):
        message = Message.objects.create(
            conversation=self.conversation, role="USER", state="ACCEPTED", text="fixture"
        )
        return StreamOperation.objects.create(
            conversation=self.conversation, user_message=message,
            idempotency_key=f"race-{timezone.now().timestamp()}", request_hash="a" * 64,
            expected_brief_revision=0,
        )

    def run_at_final_publication(self, operation, mutate):
        final_boundary = threading.Event()
        release = threading.Event()

        real_finalize = streaming.finalize_operation

        def blocked_finalize(*args, **kwargs):
            final_boundary.set()
            self.assertTrue(release.wait(5), "test barrier was not released")
            return real_finalize(*args, **kwargs)

        self.assertTrue(reserve_execution_slot())
        with (
            patch("analysis.conversation.streaming.FixtureGenerator.generate", return_value=iter(["دلتای کنترل‌شده"])),
            patch("analysis.conversation.streaming.finalize_operation", side_effect=blocked_finalize),
        ):
            worker = threading.Thread(target=_execute, args=(operation.id,))
            worker.start()
            self.assertTrue(final_boundary.wait(5), "fixture worker did not reach final publication barrier")
            mutate()
            release.set()
            worker.join(5)
            self.assertFalse(worker.is_alive(), "fixture worker did not terminate")

    def test_brief_edit_prevents_late_final_publication(self):
        operation = self.operation()

        def edit():
            response = self.client.patch(
                f"/api/v1/conversations/{self.conversation.id}/brief",
                {"expected_revision": 0, "changes": {"category": "رایانه"}},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200, response.content)

        self.run_at_final_publication(operation, edit)
        operation.refresh_from_db()
        self.assertEqual(operation.status, "INTERRUPTED")
        self.assertIsNone(operation.final_message_id)

    def test_explicit_cancel_wins_before_late_final_publication(self):
        operation = self.operation()
        self.run_at_final_publication(
            operation,
            lambda: self.assertEqual(
                self.client.post(
                    f"/api/v1/operations/{operation.id}/cancel", {}, content_type="application/json"
                ).status_code,
                202,
            ),
        )
        operation.refresh_from_db()
        self.assertEqual(operation.status, "CANCELLED")
        self.assertIsNone(operation.final_message_id)

    def test_delete_invalidates_worker_publication(self):
        operation = self.operation()
        self.run_at_final_publication(
            operation,
            lambda: self.assertEqual(
                self.client.delete(f"/api/v1/conversations/{self.conversation.id}").status_code,
                204,
            ),
        )
        self.assertFalse(StreamOperation.objects.filter(id=operation.id).exists())

    def test_stale_pending_operation_becomes_interrupted_without_restart(self):
        operation = self.operation()
        StreamOperation.objects.filter(id=operation.id).update(created_at=timezone.now() - timedelta(minutes=1))
        operation.refresh_from_db()
        reconciled = reconcile_stale_operation(operation)
        self.assertEqual(reconciled.status, "INTERRUPTED")
        self.assertEqual(reconciled.terminal_code, "WORKER_INTERRUPTED")
        self.assertIsNone(reconciled.final_message_id)

    def test_final_message_and_both_events_commit_atomically(self):
        operation = self.operation()
        self.assertTrue(claim_operation(operation.id, "test-worker"))
        self.assertTrue(finalize_operation(operation.id, "test-worker", "پاسخ نهایی"))
        operation.refresh_from_db()
        self.assertEqual(operation.status, "COMPLETED")
        self.assertEqual(operation.final_message.state, "FINAL")
        self.assertEqual(
            list(operation.events.values_list("event_type", flat=True)),
            ["assistant.message.final", "operation.completed"],
        )

    def test_failure_during_second_final_event_rolls_back_everything(self):
        operation = self.operation()
        self.assertTrue(claim_operation(operation.id, "test-worker"))
        real_create = StreamEvent.objects.create
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected final event failure")
            return real_create(*args, **kwargs)

        with patch("analysis.conversation.streaming.StreamEvent.objects.create", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                finalize_operation(operation.id, "test-worker", "نباید بماند")
        operation.refresh_from_db()
        self.assertEqual(operation.status, "RUNNING")
        self.assertIsNone(operation.final_message_id)
        self.assertFalse(Message.objects.filter(conversation=self.conversation, role="ASSISTANT").exists())
        self.assertFalse(StreamEvent.objects.filter(operation=operation).exists())

    def test_cancel_wins_before_finalization_and_completion_wins_after_commit(self):
        operation = self.operation()
        self.assertTrue(claim_operation(operation.id, "test-worker"))
        from analysis.conversation.streaming import cancel_operation
        cancelled, _ = cancel_operation(operation.id)
        self.assertTrue(cancelled)
        self.assertFalse(finalize_operation(operation.id, "test-worker", "late"))
        operation.refresh_from_db()
        self.assertEqual(operation.status, "CANCELLED")
        self.assertIsNone(operation.final_message_id)

        completed = self.operation()
        self.assertTrue(claim_operation(completed.id, "test-worker"))
        self.assertTrue(finalize_operation(completed.id, "test-worker", "winner"))
        cancelled, terminal = cancel_operation(completed.id)
        self.assertFalse(cancelled)
        self.assertEqual(terminal.status, "COMPLETED")

    def test_lost_lease_owner_cannot_publish_final(self):
        operation = self.operation()
        self.assertTrue(claim_operation(operation.id, "first-worker"))
        StreamOperation.objects.filter(id=operation.id).update(lease_owner="replacement-worker")
        self.assertFalse(finalize_operation(operation.id, "first-worker", "late"))
        self.assertFalse(StreamEvent.objects.filter(operation=operation).exists())

    def test_reconciler_rechecks_fresh_renewed_lease_under_lock(self):
        operation = self.operation()
        self.assertTrue(claim_operation(operation.id, "test-worker"))
        stale_snapshot = StreamOperation.objects.get(id=operation.id)
        stale_snapshot.lease_expires_at = timezone.now() - timedelta(seconds=1)
        self.assertTrue(renew_operation_lease(operation.id, "test-worker"))
        reconciled = reconcile_stale_operation(stale_snapshot)
        self.assertEqual(reconciled.status, "RUNNING")
        self.assertFalse(StreamEvent.objects.filter(operation=operation, event_type="operation.failed").exists())
