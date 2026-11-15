import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import CopilotSettings, GuestContext, UserCredential


class ProviderCredentialTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=2))

    def test_gapgpt_key_has_separate_provider_record_and_preserves_openai_ciphertext(self):
        from analysis.ai.provider_credentials import decrypt_provider_credential, save_provider_credential
        from analysis.models import ProviderCredential

        legacy = UserCredential.objects.create(
            guest_context=self.guest, ciphertext="legacy-openai-ciphertext", wrapped_key="legacy-wrapped",
            state="STORED_UNVALIDATED", expires_at=timezone.now() + timedelta(days=1),
        )
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / "keyring"
            keyfile.write_bytes(Fernet.generate_key())
            keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)):
                row = save_provider_credential(self.guest, "gapgpt", "synthetic-gapgpt-key-123")
                self.assertEqual(decrypt_provider_credential(self.guest.id, "gapgpt", row.revision),
                                 "synthetic-gapgpt-key-123")

        legacy.refresh_from_db()
        self.assertEqual(legacy.ciphertext, "legacy-openai-ciphertext")
        self.assertEqual(ProviderCredential.objects.get().provider, "gapgpt")

    def test_settings_and_credential_writes_make_no_provider_call(self):
        from analysis.models import ProviderCredential

        CopilotSettings.objects.create(guest_context=self.guest, provider="gapgpt",
                                       model="gapgpt-deepseek-v4.1-flash")
        session = self.client.session
        session["guest_context_id"] = str(self.guest.id)
        session.save()
        with tempfile.TemporaryDirectory() as directory:
            keyfile = Path(directory) / "keyring"
            keyfile.write_bytes(Fernet.generate_key())
            keyfile.chmod(0o600)
            with override_settings(COPILOT_MASTER_KEY_FILE=str(keyfile)), \
                    patch("analysis.ai.gapgpt_copilot.sdk_chat_events", side_effect=AssertionError("network forbidden")):
                response = self.client.put(
                    "/api/v1/copilot/credential",
                    {"provider": "gapgpt", "key": "synthetic-gapgpt-key-123", "expected_revision": None},
                    content_type="application/json",
                )
                settings_response = self.client.get("/api/v1/copilot/settings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "gapgpt")
        self.assertEqual(response.json()["state"], "STORED_UNVALIDATED")
        self.assertEqual(settings_response.json()["provider"], "gapgpt")
        self.assertEqual(ProviderCredential.objects.count(), 1)
