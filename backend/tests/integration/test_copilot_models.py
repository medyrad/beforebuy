from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from analysis.models import Conversation, GuestContext, ShoppingBrief, StreamEvent, StreamOperation


class CopilotModelTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.conversation = Conversation.objects.create_for_guest(self.guest, title="خرید بعدی")

    def test_conversation_factory_creates_revision_zero_brief(self):
        brief = ShoppingBrief.objects.get(conversation=self.conversation)
        self.assertEqual(brief.revision, 0)
        self.assertIsNone(brief.budget_toman)
        self.assertIn("بودجه", brief.unknowns)
        self.assertEqual(self.conversation.expires_at.date(), (timezone.now() + timedelta(days=90)).date())

    def test_zero_budget_is_distinct_from_unknown(self):
        brief = self.conversation.brief
        brief.budget_toman = 0
        brief.save(update_fields=["budget_toman"])
        brief.refresh_from_db()
        self.assertEqual(brief.budget_toman, 0)

    def test_operation_idempotency_and_event_sequence_are_unique(self):
        operation = StreamOperation.objects.create(
            conversation=self.conversation,
            idempotency_key="model-test-key-0001",
            request_hash="0" * 64,
            expected_brief_revision=0,
        )
        StreamEvent.objects.create(operation=operation, sequence=1, event_type="operation.started", payload={})
        with self.assertRaises(IntegrityError), transaction.atomic():
            StreamEvent.objects.create(operation=operation, sequence=1, event_type="operation.started", payload={})
