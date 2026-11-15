from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from analysis.models import Conversation, CopilotSettings, GuestContext, UserCredential
from tests.api.test_conversations import csrf_client


class ConversationalUXApiTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        self.guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])

    def test_clear_preserves_independent_credentials_settings_and_other_owners(self):
        Conversation.objects.create_for_guest(self.guest)
        settings = CopilotSettings.objects.create(guest_context=self.guest, provider='openai', model='gpt-6-luna')
        key = UserCredential.objects.create(guest_context=self.guest, ciphertext='synthetic', wrapped_key='synthetic',
            expires_at=timezone.now()+timedelta(days=1), state='STORED_UNVALIDATED')
        stranger = GuestContext.objects.create(access_expires_at=timezone.now()+timedelta(days=1))
        other = Conversation.objects.create_for_guest(stranger)
        self.assertEqual(self.client.delete('/api/v1/conversations').status_code, 403)
        response = self.client.delete('/api/v1/conversations', HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Conversation.objects.filter(guest_context=self.guest).exists())
        self.assertTrue(Conversation.objects.filter(id=other.id).exists())
        key.refresh_from_db(); settings.refresh_from_db()
        self.assertEqual(key.ciphertext, 'synthetic')
        self.assertEqual(settings.provider, 'openai')

    def test_settings_distinguish_saved_state_from_region_connection_block(self):
        CopilotSettings.objects.create(guest_context=self.guest, provider='openai', model='gpt-6-luna')
        UserCredential.objects.create(guest_context=self.guest, ciphertext='synthetic', wrapped_key='synthetic',
            expires_at=timezone.now()+timedelta(days=1), state='STORED_UNVALIDATED')
        result = self.client.get('/api/v1/copilot/settings').json()
        self.assertEqual(result['credential_state'], 'STORED_UNVALIDATED')
        self.assertEqual(result['connection'], 'VALIDATION_BLOCKED')
        self.assertEqual(result['mode'], 'DEMONSTRATION')

    @patch('analysis.api.conversations.reserve_execution_slot', return_value=True)
    @patch('analysis.api.conversations.submit_reserved')
    def test_malformed_answer_and_boolean_revision_rejected(self, _submit, _reserve):
        c = Conversation.objects.create_for_guest(self.guest)
        for data in [{'answer': []}, {'expected_brief_revision': True}]:
            response = self.client.post(f'/api/v1/conversations/{c.id}/messages',
                {'text': 'test', 'expected_brief_revision': 0} | data, content_type='application/json',
                HTTP_X_CSRFTOKEN=self.token, HTTP_IDEMPOTENCY_KEY='ux-malformed-key-0001')
            self.assertEqual(response.status_code, 422)
        self.assertEqual(c.messages.count(), 0)
