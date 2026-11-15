"""Small Fernet envelope; master keyring only in a runtime file, never in DB."""
import json
import uuid
from pathlib import Path
from datetime import timedelta
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from analysis.models import GuestContext, UserCredential


class CredentialUnavailable(ValueError):
    def __init__(self):
        super().__init__('CREDENTIAL_UNAVAILABLE')


@sensitive_variables()
def keyring():
    try:
        path = Path(settings.COPILOT_MASTER_KEY_FILE)
        if not settings.COPILOT_MASTER_KEY_FILE or path.stat().st_size > 4096:
            raise ValueError
        keys = path.read_bytes().splitlines()
        if not 1 <= len(keys) <= 5:
            raise ValueError
        return MultiFernet([Fernet(k.strip()) for k in keys])
    except (OSError, ValueError, TypeError):
        raise CredentialUnavailable() from None


def active_credential(guest_id):
    return UserCredential.objects.filter(guest_context_id=guest_id, expires_at__gt=timezone.now(),
        guest_context__access_expires_at__gt=timezone.now()).first()


@sensitive_variables()
def encrypt_for_owner(guest, plaintext):
    ring = keyring()
    data_key = Fernet.generate_key()
    payload = json.dumps({'owner': str(guest.id), 'key': plaintext}).encode()
    return Fernet(data_key).encrypt(payload).decode(), ring.encrypt(data_key).decode()


@sensitive_variables()
def decrypt_current(guest_id, expected_revision):
    row = active_credential(guest_id)
    if row is None or str(row.revision) != str(expected_revision):
        raise CredentialUnavailable()
    try:
        data_key = keyring().decrypt(row.wrapped_key.encode())
        payload = json.loads(Fernet(data_key).decrypt(row.ciphertext.encode()))
        if payload['owner'] != str(guest_id):
            raise ValueError
        return payload['key']
    except (InvalidToken, ValueError, KeyError, TypeError):
        raise CredentialUnavailable() from None


@sensitive_variables()
@transaction.atomic
def save_credential(guest, plaintext):
    GuestContext.objects.select_for_update().get(id=guest.id)
    ciphertext, wrapped = encrypt_for_owner(guest, plaintext)
    invalidate_credential_operations(guest.id)
    row, _ = UserCredential.objects.update_or_create(guest_context=guest, defaults={
        'ciphertext': ciphertext, 'wrapped_key': wrapped, 'revision': uuid.uuid4(), 'state': 'STORED_UNVALIDATED',
        'expires_at': min(guest.access_expires_at, timezone.now()+timedelta(days=settings.COPILOT_CREDENTIAL_DAYS))})
    return row


def invalidate_credential_operations(guest_id):
    from analysis.models import StreamOperation
    from analysis.conversation.streaming import cancel_operation
    # Guest already locked by caller; cancel uses Conversation -> Operation locks.
    ids = StreamOperation.objects.filter(conversation__guest_context_id=guest_id,
        credential_revision__isnull=False, status__in=['PENDING', 'RUNNING']).order_by('conversation_id', 'id').values_list('id', flat=True)
    for operation_id in list(ids):
        cancel_operation(operation_id)


@sensitive_variables()
def rotate_credentials():
    ring = keyring()
    count = 0
    # Same guest lock as replace/delete; all-or-nothing rotation, no plaintext API keys exposed.
    with transaction.atomic():
        for guest in GuestContext.objects.select_for_update().filter(credential__isnull=False).order_by('id'):
            row = UserCredential.objects.get(guest_context=guest)
            try:
                row.wrapped_key = ring.rotate(row.wrapped_key.encode()).decode()
            except InvalidToken:
                raise CredentialUnavailable() from None
            row.save(update_fields=['wrapped_key'])
            count += 1
    return count
