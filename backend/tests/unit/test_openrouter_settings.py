from unittest.mock import patch
from django.test import TestCase
from analysis.models import CopilotSettings, GuestContext
from django.test import override_settings


class OpenRouterSettingsTests(TestCase):
    @override_settings(COPILOT_OPENROUTER_SERVICE_ELIGIBLE=True, COPILOT_OPENROUTER_ROUTE_ELIGIBLE=True,
                       COPILOT_OPENROUTER_ELIGIBILITY_REFERENCE='synthetic', COPILOT_AI_MODE='mock')
    def test_explicit_stub_validation_creates_isolated_pilot_and_publishes_with_own_key(self):
        from tests.unit.test_openrouter_copilot import OpenRouterTests
        import tempfile
        from pathlib import Path
        from cryptography.fernet import Fernet
        from analysis.ai.provider_catalog import OPENROUTER_MODEL
        from analysis.ai.provider_credentials import save_provider_credential, decrypt_provider_credential
        from analysis.models import Conversation, ProviderCredential, Message, StreamOperation
        from analysis.conversation.streaming import finalize_operation
        from django.utils import timezone
        from datetime import timedelta
        self.client.get('/api/v1/copilot/settings')
        guest = GuestContext.objects.get()
        CopilotSettings.objects.update(provider='openrouter', model=OPENROUTER_MODEL)
        fixture = OpenRouterTests()
        fixture.guest = guest
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / 'synthetic-keyring'
            keyfile.write_bytes(Fernet.generate_key()); keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)), \
                    patch('analysis.ai.openrouter_copilot.current_prices', return_value={'prompt': '0', 'completion': '0'}), \
                    patch('analysis.ai.openrouter_copilot.sdk_events', fixture.adapter().transport):
                gap = save_provider_credential(guest, 'gapgpt', 'synthetic-gapgpt-12345')
                row = save_provider_credential(guest, 'openrouter', 'synthetic-openrouter-12345')
                self.assertEqual(decrypt_provider_credential(guest.id, 'gapgpt', gap.revision), 'synthetic-gapgpt-12345')
                response = self.client.post('/api/v1/copilot/models/refresh', {'synthetic_consent': True}, content_type='application/json')
                self.assertEqual(response.status_code, 200, response.content)
                conversation = Conversation.objects.get(id=response.json()['conversation_id'])
                self.assertTrue(conversation.temporary and conversation.openrouter_pilot)
                row.refresh_from_db()
                self.assertEqual(row.state, 'VALIDATED')
                message = Message.objects.create(conversation=conversation, role='USER', state='ACCEPTED', text='گوشی من شکسته می‌خواهم آیفون ده بخرم.')
                operation = StreamOperation.objects.create(conversation=conversation, user_message=message,
                    idempotency_key='synthetic-openrouter-final', request_hash='1' * 64,
                    expected_brief_revision=conversation.brief_revision, status='RUNNING', lease_owner='synthetic',
                    lease_expires_at=timezone.now() + timedelta(minutes=1), credential_provider='openrouter', credential_revision=row.revision)
                from analysis.ai.copilot_factory import configured_copilot_generator
                generator = configured_copilot_generator(operation.id)
                self.assertEqual(generator.kind, 'OPENROUTER_FREE_CHAT')
                chunks = list(generator.generate())
                self.assertEqual(chunks[-1]['phase'], 'VALIDATED_BLOCK')
                finalize_operation(operation.id, 'synthetic', generator.final_text)
                operation.refresh_from_db()
                self.assertEqual(operation.status, 'COMPLETED')
                self.assertEqual(ProviderCredential.objects.get(provider='gapgpt').state, 'STORED_UNVALIDATED')
                from analysis.ai.openai_copilot import CopilotProviderError
                with patch('analysis.ai.openrouter_copilot.sdk_events', side_effect=CopilotProviderError('OPENROUTER_AUTH_FAILED')):
                    failed = self.client.post('/api/v1/copilot/models/refresh', {'synthetic_consent': True}, content_type='application/json')
                self.assertEqual(failed.status_code, 409)
                row.refresh_from_db()
                self.assertEqual(row.state, 'VALIDATION_FAILED')

    def test_catalog_and_separate_readiness_without_network(self):
        response = self.client.get('/api/v1/copilot/settings').json()
        response = self.client.patch('/api/v1/copilot/settings', {
            'provider': 'openrouter', 'expected_revision': response['revision'],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['openrouter']['service_eligible'])
        self.assertFalse(data['openrouter']['data_consent'])
        self.assertEqual(data['openrouter']['remaining_attempts'], 10)
        self.assertEqual(data['provider'], 'openrouter')
        with patch('analysis.ai.openrouter_copilot.sdk_events', side_effect=AssertionError('no network')):
            result = self.client.post('/api/v1/copilot/models/refresh', {'synthetic_consent': True}, content_type='application/json')
        self.assertEqual(result.status_code, 409)
        self.assertEqual(result.json()['error']['code'], 'SERVICE_ELIGIBILITY_REQUIRED')

    def test_explicit_consent_required_even_with_key(self):
        self.client.get('/api/v1/copilot/settings')
        CopilotSettings.objects.update(provider='openrouter')
        response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'SYNTHETIC_CONSENT_REQUIRED')
