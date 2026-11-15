import tempfile
from pathlib import Path
from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from tests.api.test_research_api import csrf_client


class CredentialTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        self.path = '/api/v1/copilot/credential'

    def write(self, method, data=None):
        return getattr(self.client, method)(self.path, data or {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token)

    def test_non_object_bodies_are_rejected_without_server_error(self):
        self.client.raise_request_exception = False
        for path, method in [(self.path, 'put'), (self.path, 'delete'), ('/api/v1/copilot/settings', 'patch')]:
            response = getattr(self.client, method)(path, '[]', content_type='application/json', HTTP_X_CSRFTOKEN=self.token)
            self.assertEqual(response.status_code, 422)

    @override_settings(COPILOT_MASTER_KEY_FILE='')
    def test_offline_without_master_and_write_fails_without_leaking(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], 'NOT_CONFIGURED')
        secret = 'synthetic-credential-not-a-real-key'
        response = self.write('put', {'key': secret, 'expected_revision': None})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(secret, response.content.decode())

    def test_envelope_replace_delete_stale_owner_rotation_and_wrong_master(self):
        from cryptography.fernet import Fernet
        from analysis.ai.credentials import decrypt_current, rotate_credentials, CredentialUnavailable
        from analysis.models import UserCredential
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / 'master'
            old = Fernet.generate_key(); new = Fernet.generate_key()
            keyfile.write_bytes(old + b'\n'); keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)):
                key = 'synthetic-credential-only-111111'
                with self.assertNoLogs(level='DEBUG'):
                    r = self.write('put', {'key': key, 'expected_revision': None})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()['state'], 'STORED_UNVALIDATED')
                row = UserCredential.objects.get()
                self.assertNotIn(key, str(row.__dict__))
                self.assertNotIn(key, r.content.decode())
                self.assertEqual(decrypt_current(row.guest_context_id, row.revision), key)
                other, _ = csrf_client()
                self.assertEqual(other.get(self.path).json()['state'], 'NOT_CONFIGURED')
                keyfile.write_bytes(new + b'\n')
                with self.assertRaises(CredentialUnavailable): decrypt_current(row.guest_context_id, row.revision)
                keyfile.write_bytes(new + b'\n' + old + b'\n')
                expiry = row.expires_at
                rotate_credentials()
                keyfile.write_bytes(new + b'\n')
                self.assertEqual(decrypt_current(row.guest_context_id, row.revision), key)
                row.refresh_from_db(); self.assertEqual(row.expires_at, expiry)
                r = self.write('put', {'key': 'synthetic-replacement-222222', 'expected_revision': str(row.revision)})
                self.assertEqual(r.status_code, 200)
                with self.assertRaises(CredentialUnavailable): decrypt_current(row.guest_context_id, row.revision)
                stale = self.write('delete', {'expected_revision': str(row.revision)})
                self.assertEqual(stale.status_code, 409)
                row.refresh_from_db()
                r = self.write('delete', {'expected_revision': str(row.revision)})
                self.assertEqual(r.status_code, 204)
                self.assertFalse(UserCredential.objects.exists())
                with self.assertRaises(CredentialUnavailable): decrypt_current(row.guest_context_id, row.revision)

    def test_csrf_and_expired_key_not_returned(self):
        self.assertEqual(self.client.put(self.path, {}, content_type='application/json').status_code, 403)
        from analysis.models import UserCredential, GuestContext
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        UserCredential.objects.create(guest_context=guest, ciphertext='not plaintext', wrapped_key='invalid',
                                      expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(self.path).json()['state'], 'NOT_CONFIGURED')

    def test_replace_revokes_queued_and_running_operations(self):
        from cryptography.fernet import Fernet
        from analysis.models import GuestContext, Conversation, StreamOperation, UserCredential
        from analysis.ai.credentials import save_credential
        from analysis.conversation.streaming import claim_operation, finalize_operation
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / 'master'; keyfile.write_bytes(Fernet.generate_key()); keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)):
                row = save_credential(guest, 'synthetic-only-credential')
                conversation = Conversation.objects.create_for_guest(guest)
                operation = StreamOperation.objects.create(conversation=conversation, credential_revision=row.revision,
                    idempotency_key='queued-synthetic-1234', request_hash='a'*64, expected_brief_revision=0)
                pending = StreamOperation.objects.create(conversation=conversation, credential_revision=row.revision,
                    idempotency_key='pending-synthetic-1234', request_hash='b'*64, expected_brief_revision=0)
                self.assertTrue(claim_operation(operation.id, 'worker'))
                response = self.write('put', {'key': 'synthetic-replaced-credential', 'expected_revision': str(row.revision)})
                self.assertEqual(response.status_code, 200)
                operation.refresh_from_db()
                self.assertEqual(operation.status, 'CANCELLED')
                pending.refresh_from_db()
                self.assertEqual(pending.status, 'CANCELLED')
                self.assertFalse(finalize_operation(operation.id, 'worker', 'late'))
                self.assertFalse(conversation.messages.exists())
                row.refresh_from_db()
                queued = StreamOperation.objects.create(conversation=conversation, credential_revision=row.revision,
                    idempotency_key='delete-synthetic-1234', request_hash='c'*64, expected_brief_revision=0)
                self.assertEqual(self.write('delete', {'expected_revision': str(row.revision)}).status_code, 204)
                queued.refresh_from_db()
                self.assertEqual(queued.status, 'CANCELLED')

    def test_expired_credential_blocks_final_publication(self):
        from analysis.models import GuestContext, Conversation, StreamOperation, UserCredential
        from analysis.conversation.streaming import claim_operation, finalize_operation
        guest = GuestContext.objects.get(id=self.client.session['guest_context_id'])
        row = UserCredential.objects.create(guest_context=guest, ciphertext='synthetic', wrapped_key='synthetic',
                                           expires_at=timezone.now()+timedelta(hours=1))
        conversation = Conversation.objects.create_for_guest(guest)
        op = StreamOperation.objects.create(conversation=conversation, credential_revision=row.revision,
            idempotency_key='expiry-synthetic-1234', request_hash='b'*64, expected_brief_revision=0)
        self.assertTrue(claim_operation(op.id, 'worker'))
        UserCredential.objects.filter(pk=row.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertFalse(finalize_operation(op.id, 'worker', 'must not publish'))
        self.assertFalse(conversation.messages.exists())
