from unittest.mock import patch

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from analysis.models import GuestContext, UserCredential


class CopilotModelRefreshTests(TestCase):
    def test_settings_read_does_not_trigger_account_discovery(self):
        with patch('analysis.ai.openai_copilot.sdk_model_ids') as transport:
            response = self.client.get('/api/v1/copilot/settings')
        self.assertEqual(response.status_code, 200)
        transport.assert_not_called()
        self.assertEqual(response.json()['catalog']['source'], 'DOCUMENTATION_UNVERIFIED')

    def test_explicit_refresh_is_region_gated_before_credential_or_transport(self):
        with patch('analysis.ai.openai_copilot.sdk_model_ids') as transport:
            response = self.client.post('/api/v1/copilot/models/refresh', {}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'REGION_BLOCKED')
        transport.assert_not_called()

    def test_explicit_eligible_refresh_intersects_account_ids_without_implicit_fallback(self):
        self.client.get('/api/v1/copilot/settings')
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
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
