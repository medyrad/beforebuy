from datetime import timedelta
import uuid

from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone

from analysis.models import Conversation, GuestContext
from analysis.conversation.operations import accept_message, OperationConflict
from analysis.conversation.streaming import _execute, reserve_execution_slot


class ExplicitBudgetGrammarTests(SimpleTestCase):
    def test_exact_units_and_ambiguous_or_non_budget_inputs(self):
        from analysis.conversation.replies import explicit_budget
        for text, value in [('۱۵ میلیون ریال', 1500000), ('بودجه‌ام ۰ تومان است', 0),
                            ('1.5 میلیون تومان', 1500000), ('بودجه: ۱۵٬۰۰۰٬۰۰۰ تومان', 15000000)]:
            self.assertEqual(explicit_budget(text), value)
        for text in ['قیمت گوشی ۲۰ میلیون تومان است', '۱۰ تا ۲۰ میلیون تومان', '۱۵ میلیون',
                     '-1 تومان', '9 ریال', '۱,۵ میلیون تومان', '10 تومان و 20 تومان']:
            self.assertIsNone(explicit_budget(text), text)


@override_settings(COPILOT_AI_MODE='mock')
class ConversationalUXTests(TransactionTestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        self.conversation = Conversation.objects.create_for_guest(self.guest)

    def send(self, text, answer=None, key=None):
        self.conversation.refresh_from_db()
        args = dict(conversation_id=self.conversation.id, guest=self.guest, text=text, upload_ids=[],
                    expected_revision=self.conversation.brief_revision, idempotency_key=key or str(uuid.uuid4()))
        if answer is not None:
            args['answer'] = answer
        op, replay = accept_message(**args)
        if not replay:
            self.assertTrue(reserve_execution_slot())
            _execute(op.id)
        op.refresh_from_db()
        self.assertEqual(op.status, 'COMPLETED', op.terminal_code)
        return op

    def test_exact_budget_regression_through_worker_context_and_publication(self):
        self.send('گوشی من شکسته، می‌خواهم آیفون ده بخرم.')
        second = self.send('بودجه‌ام ۱۵ میلیون تومان است')
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.brief.budget_toman, 15_000_000)
        self.assertFalse(self.conversation.brief.confirmed)
        self.assertNotIn('سقف بودجهٔ این خرید چقدر است', second.final_message.text)
        third = self.send('۱۵ میلیون ریال')
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.brief.budget_toman, 15_000_000)
        actions = third.final_message.reply_actions
        self.assertEqual(len(actions), 2)
        self.assertIn('۱٬۵۰۰٬۰۰۰', third.final_message.text)
        action = actions[0]
        answer = {'question_id': action['question_id'], 'action_id': action['id'], 'revision': action['revision']}
        self.send(action['label'], answer)
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.brief.budget_toman, 1_500_000)
        self.assertFalse(self.conversation.brief.conversation_state)
        with self.assertRaises(OperationConflict):
            self.send(action['label'], answer)

    def test_typed_keep_and_amount_disambiguation(self):
        self.send('بودجه‌ام ۱۵ میلیون تومان است')
        self.send('۱۵ میلیون ریال')
        self.send('همان بودجهٔ قبلی')
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.brief.budget_toman, 15_000_000)
        self.assertFalse(self.conversation.brief.conversation_state)

    def test_manual_confirmation_invalidates_older_question_even_without_revision_change(self):
        first = self.send('بودجه‌ام ۱۵ میلیون تومان است')
        action = first.final_message.reply_actions[0]
        brief = self.conversation.brief
        brief.confirmed = True
        brief.save(update_fields=['confirmed', 'updated_at'])
        with self.assertRaises(OperationConflict):
            self.send(action['label'], {'question_id': action['question_id'], 'action_id': action['id'], 'revision': action['revision']})
        self.send('این یک پیام تازه است')
        self.conversation.refresh_from_db()
        self.assertIsNone(self.conversation.brief.category)
        self.assertTrue(self.conversation.brief.confirmed)

    def test_action_replay_is_idempotent_and_foreign_question_rejected(self):
        first = self.send('بودجه‌ام ۱۵ میلیون تومان است')
        action = first.final_message.reply_actions[0]
        answer = {'question_id': action['question_id'], 'action_id': action['id'], 'revision': action['revision']}
        args = dict(conversation_id=self.conversation.id, guest=self.guest, text=action['label'], upload_ids=[],
                    expected_revision=action['revision'], idempotency_key='ux-action-replay-001', answer=answer)
        op, replay = accept_message(**args)
        same, replay = accept_message(**args)
        self.assertTrue(replay)
        self.assertEqual(op.id, same.id)
        other = Conversation.objects.create_for_guest(self.guest)
        with self.assertRaises(OperationConflict):
            accept_message(**(args | {'conversation_id': other.id, 'expected_revision': 0,
                                     'idempotency_key': 'ux-foreign-action-001'}))
