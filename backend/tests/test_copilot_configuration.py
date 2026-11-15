from unittest.mock import patch
from django.test import TestCase, TransactionTestCase, override_settings
from tests.api.test_research_api import csrf_client


class CopilotConfigurationTests(TestCase):
    @override_settings(COPILOT_AI_MODE='live', COPILOT_OPERATION_CAP_MICROUSD=10000,
                       COPILOT_SESSION_CAP_MICROUSD=20000, COPILOT_DAILY_CAP_MICROUSD=100000)
    def test_factory_assembles_adapter_after_test_only_eligibility_stub(self):
        from analysis.models import GuestContext, Conversation, UserCredential
        from analysis.conversation.operations import accept_message
        from analysis.conversation.streaming import claim_operation
        from analysis.ai.openai_copilot import configured_copilot_generator, OpenAICopilotGenerator
        from django.utils import timezone
        from datetime import timedelta
        guest = GuestContext.objects.create(access_expires_at=timezone.now()+timedelta(days=1))
        convo = Conversation.objects.create_for_guest(guest)
        credential = UserCredential.objects.create(guest_context=guest, ciphertext='synthetic', wrapped_key='synthetic',
            state='VALIDATED', expires_at=timezone.now()+timedelta(hours=1))
        with patch('analysis.ai.openai_copilot.ensure_live_eligible'), patch('analysis.ai.openai_copilot.sdk_events') as transport:
            op, _ = accept_message(conversation_id=convo.id, guest=guest, text='بودجه نامعلوم', upload_ids=[],
                                   expected_revision=0, idempotency_key='factory-synthetic-1234')
            self.assertEqual(op.credential_revision, credential.revision)
            self.assertTrue(claim_operation(op.id, 'factory-worker'))
            adapter = configured_copilot_generator(op.id)
            self.assertIsInstance(adapter, OpenAICopilotGenerator)
            self.assertTrue(adapter.still_current())
            self.assertEqual(adapter.context['current_message'], 'بودجه نامعلوم')
            credential.delete()
            self.assertFalse(adapter.still_current())
            transport.assert_not_called()


class CopilotWorkerTranslationTests(TransactionTestCase):
    @override_settings(COPILOT_AI_MODE='live', COPILOT_OPERATION_CAP_MICROUSD=10000,
                       COPILOT_SESSION_CAP_MICROUSD=20000, COPILOT_DAILY_CAP_MICROUSD=100000)
    def test_stubbed_provider_worker_is_not_labelled_development_fixture(self):
        import tempfile
        from pathlib import Path
        from datetime import timedelta
        from cryptography.fernet import Fernet
        from django.utils import timezone
        from analysis.models import GuestContext, Conversation
        from analysis.ai.credentials import save_credential
        from analysis.conversation.operations import accept_message
        from analysis.conversation.streaming import _execute, reserve_execution_slot
        guest = GuestContext.objects.create(access_expires_at=timezone.now()+timedelta(days=1))
        convo = Conversation.objects.create_for_guest(guest)
        events = [{'type': 'response.output_text.delta', 'delta': '{"answer_type":"CLARIFICATION",'
                   '"lead_key":"NEEDS_CONTEXT","clarification_key":"budget_toman","blocks":[]}'},
                  {'type': 'response.completed', 'response': {'status': 'completed',
                   'usage': {'input_tokens': 40, 'output_tokens': 10}}}]
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory)/'key'; keyfile.write_bytes(Fernet.generate_key()); keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)), \
                    patch('analysis.ai.openai_copilot.ensure_live_eligible'), \
                    patch('analysis.ai.openai_copilot.sdk_events', return_value=iter(events)):
                key = save_credential(guest, 'synthetic-worker-only')
                key.state = 'VALIDATED'; key.save(update_fields=['state'])
                op, _ = accept_message(conversation_id=convo.id, guest=guest, text='بودجه؟', upload_ids=[],
                    expected_revision=0, idempotency_key='synthetic-worker-1234')
                self.assertTrue(reserve_execution_slot())
                _execute(op.id)
        op.refresh_from_db()
        self.assertEqual(op.status, 'COMPLETED')
        self.assertEqual(op.final_message.text, 'سقف بودجهٔ این خرید چقدر است؟')
        self.assertEqual(op.events.get(event_type='operation.started').payload['kind'], 'OPENAI_RESPONSE')

    def test_default_factory_is_offline_without_master_key(self):
        from analysis.ai.openai_copilot import configured_copilot_generator
        with override_settings(COPILOT_MASTER_KEY_FILE='', COPILOT_AI_MODE='mock'):
            self.assertIn('fixture', ''.join(configured_copilot_generator(None).generate()))

    @override_settings(COPILOT_AI_MODE='live', COPILOT_OPERATION_CAP_MICROUSD=999999,
                       COPILOT_SESSION_CAP_MICROUSD=999999, COPILOT_REGION_REVIEWED=True)
    def test_live_submission_and_factory_block_before_transport(self):
        from analysis.ai.openai_copilot import configured_copilot_generator, CopilotProviderError
        client, token = csrf_client()
        c = client.post('/api/v1/conversations', {}, content_type='application/json', HTTP_X_CSRFTOKEN=token).json()
        with patch('analysis.ai.openai_copilot.sdk_events', side_effect=AssertionError('network forbidden')) as transport:
            response = client.post(f'/api/v1/conversations/{c["id"]}/messages', {'text': 'test', 'expected_brief_revision': 0},
                content_type='application/json', HTTP_X_CSRFTOKEN=token, HTTP_IDEMPOTENCY_KEY='synthetic-key-123456')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()['error']['code'], 'REGION_BLOCKED')
            with self.assertRaisesRegex(CopilotProviderError, 'REGION_BLOCKED'):
                configured_copilot_generator(None)
            transport.assert_not_called()
