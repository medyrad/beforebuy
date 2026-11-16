"""Provider-bound encrypted credentials; historical OpenAI rows are untouched."""
import json
import uuid
from datetime import timedelta

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from analysis.models import GuestContext, ProviderCredential
from .credentials import CredentialUnavailable, keyring

SUPPORTED_PROVIDERS = {"gapgpt", "openrouter"}


def active_provider_credential(guest_id, provider):
    if provider not in SUPPORTED_PROVIDERS:
        return None
    return ProviderCredential.objects.filter(
        guest_context_id=guest_id, provider=provider, expires_at__gt=timezone.now(),
        guest_context__access_expires_at__gt=timezone.now(),
    ).first()


@sensitive_variables()
def _encrypt(guest, provider, plaintext):
    ring = keyring()
    data_key = Fernet.generate_key()
    payload = json.dumps({"owner": str(guest.id), "provider": provider, "key": plaintext}).encode()
    return Fernet(data_key).encrypt(payload).decode(), ring.encrypt(data_key).decode()


@sensitive_variables()
def decrypt_provider_credential(guest_id, provider, expected_revision):
    row = active_provider_credential(guest_id, provider)
    if row is None or str(row.revision) != str(expected_revision):
        raise CredentialUnavailable()
    try:
        data_key = keyring().decrypt(row.wrapped_key.encode())
        payload = json.loads(Fernet(data_key).decrypt(row.ciphertext.encode()))
        if payload["owner"] != str(guest_id) or payload["provider"] != provider:
            raise ValueError
        return payload["key"]
    except (InvalidToken, ValueError, KeyError, TypeError):
        raise CredentialUnavailable() from None


@sensitive_variables()
@transaction.atomic
def save_provider_credential(guest, provider, plaintext):
    if provider not in SUPPORTED_PROVIDERS:
        raise CredentialUnavailable()
    GuestContext.objects.select_for_update().get(id=guest.id)
    ciphertext, wrapped = _encrypt(guest, provider, plaintext)
    invalidate_provider_operations(guest.id, provider)
    row, _ = ProviderCredential.objects.update_or_create(
        guest_context=guest, provider=provider,
        defaults={"ciphertext": ciphertext, "wrapped_key": wrapped, "revision": uuid.uuid4(),
                  "state": "STORED_UNVALIDATED",
                  "expires_at": min(guest.access_expires_at,
                                    timezone.now() + timedelta(days=settings.COPILOT_CREDENTIAL_DAYS))},
    )
    return row


def invalidate_provider_operations(guest_id, provider):
    from analysis.conversation.streaming import cancel_operation
    from analysis.models import StreamOperation
    ids = StreamOperation.objects.filter(
        conversation__guest_context_id=guest_id, credential_provider=provider,
        status__in=["PENDING", "RUNNING"],
    ).order_by("conversation_id", "id").values_list("id", flat=True)
    for operation_id in list(ids):
        cancel_operation(operation_id)
