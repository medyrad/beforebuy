from unittest.mock import patch

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import CopilotSettings, GuestContext, ProviderCredential, UserCredential


class CopilotModelRefreshTests(TestCase):
    def test_settings_read_does_not_trigger_account_discovery(self):
        with patch('analysis.ai.openai_copilot.sdk_model_ids') as transport:
            response = self.client.get('/api/v1/copilot/settings')
        self.assertEqual(response.status_code, 200)
        transport.assert_not_called()
        self.assertEqual(response.json()['catalog']['source'], 'DOCUMENTATION_UNVERIFIED')

    def test_explicit_gapgpt_refresh_requires_credential_without_transport(self):
        with patch('analysis.ai.openai_copilot.sdk_model_ids') as transport:
            response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'CREDENTIAL_UNVALIDATED')
        transport.assert_not_called()

    def test_explicit_gapgpt_refresh_is_blocked_without_billable_validation(self):
        self.client.get('/api/v1/copilot/settings')
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        ProviderCredential.objects.create(
            guest_context=guest, provider='gapgpt', ciphertext='synthetic', wrapped_key='synthetic',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        with patch('analysis.ai.gapgpt_copilot.sdk_chat_events') as transport:
            response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'SPENDING_AUTHORIZATION_REQUIRED')
        transport.assert_not_called()

    @override_settings(
        COPILOT_PHASE12_SPENDING_AUTHORIZED=True, COPILOT_USD_TO_TOMAN_RATE=100000,
        COPILOT_PHASE12_TOTAL_CAP_TOMAN=50000, COPILOT_OPERATION_CAP_MICROUSD=10000,
        COPILOT_SESSION_CAP_MICROUSD=20000, COPILOT_DAILY_CAP_MICROUSD=100000,
    )
    def test_explicit_authorized_gapgpt_validation_is_stubbed_accounted_and_marks_exact_credential(self):
        import json
        import tempfile
        from pathlib import Path
        from cryptography.fernet import Fernet
        from analysis.ai.provider_credentials import save_provider_credential
        self.client.get('/api/v1/copilot/settings')
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        payload = json.dumps({
            'conversation': {
                'acknowledgement': 'اتصال برای آزمون مصنوعی بررسی شد.',
                'next_question': 'چه نوع محصولی نیاز دارید؟', 'brief_proposal': {},
            },
            'answer_plan': {'answer_type': 'CLARIFICATION', 'lead_key': 'NEEDS_CONTEXT',
                            'clarification_key': 'none', 'blocks': []},
        }, ensure_ascii=False)
        events = [
            {'type': 'response.output_text.delta', 'delta': payload},
            {'type': 'response.completed', 'response': {'status': 'completed',
                'usage': {'input_tokens': 50, 'output_tokens': 20}}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / 'key'
            keyfile.write_bytes(Fernet.generate_key())
            keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)), \
                    patch('analysis.ai.gapgpt_copilot.sdk_chat_events', return_value=iter(events)) as transport:
                credential = save_provider_credential(guest, 'gapgpt', 'synthetic-gapgpt-key')
                response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['saved_status'], 'AVAILABLE')
        credential.refresh_from_db()
        self.assertEqual(credential.state, 'VALIDATED')
        transport.assert_called_once()

    def test_explicit_eligible_refresh_intersects_account_ids_without_implicit_fallback(self):
        self.client.get('/api/v1/copilot/settings')
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        CopilotSettings.objects.filter(guest_context=guest).update(provider='openai', model='gpt-6-luna')
        UserCredential.objects.create(
            guest_context=guest, ciphertext='synthetic', wrapped_key='synthetic', state='VALIDATED',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        with patch('analysis.ai.openai_copilot.ensure_live_eligible'), \
                patch('analysis.ai.openai_copilot.sdk_model_ids', return_value=['not-supported']):
            # The view imports decrypt_current locally, so patch its defining module.
            with patch('analysis.ai.credentials.decrypt_current', return_value='synthetic-not-real'):
                response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])
        self.assertEqual(response.json()['saved_status'], 'UNAVAILABLE')
