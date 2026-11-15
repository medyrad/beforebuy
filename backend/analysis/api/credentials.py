from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.response import Response
from analysis.guest import get_or_create_guest
from analysis.ai.credentials import active_credential, save_credential, keyring, CredentialUnavailable, invalidate_credential_operations
from analysis.ai.provider_credentials import (
    SUPPORTED_PROVIDERS, active_provider_credential, invalidate_provider_operations, save_provider_credential,
)
from analysis.models import CopilotSettings, ProviderCredential
from .base import ObjectBodyAPIView
from .memory import lock_guest
from .conversations import error


@method_decorator(sensitive_post_parameters('key'), name='dispatch')
class CredentialView(ObjectBodyAPIView):
    def _provider(self, request):
        explicit = request.data.get('provider') if request.method != 'GET' else request.query_params.get('provider')
        if explicit:
            return explicit
        item, _ = CopilotSettings.objects.get_or_create(guest_context=get_or_create_guest(request))
        return item.provider

    def get(self, request):
        provider = self._provider(request)
        if provider not in {'openai', *SUPPORTED_PROVIDERS}:
            return error('PROVIDER_UNAVAILABLE', 'ارائه‌دهنده پشتیبانی نمی‌شود.', 422)
        guest_id = get_or_create_guest(request).id
        row = active_credential(guest_id) if provider == 'openai' else active_provider_credential(guest_id, provider)
        try:
            keyring()
            encryption_available = True
        except CredentialUnavailable:
            encryption_available = False
        response = Response({'provider': provider, 'state': row.state if row else 'NOT_CONFIGURED', 'masked': '••••••••' if row else None,
            'revision': str(row.revision) if row else None, 'expires_at': row.expires_at.isoformat() if row else None,
            'encryption_available': encryption_available, 'validation': 'UNAVAILABLE_BLOCKED'})
        response['Cache-Control'] = 'private, no-store'
        return response

    @transaction.atomic
    def put(self, request):
        guest = lock_guest(request)
        provider = self._provider(request)
        if provider not in {'openai', *SUPPORTED_PROVIDERS}:
            return error('PROVIDER_UNAVAILABLE', 'ارائه‌دهنده پشتیبانی نمی‌شود.', 422)
        row = active_credential(guest.id) if provider == 'openai' else active_provider_credential(guest.id, provider)
        if request.data.get('expected_revision') != (str(row.revision) if row else None):
            return error('STALE_CREDENTIAL', 'کلید تغییر کرده؛ وضعیت را تازه کنید.', 409)
        value = request.data.get('key')
        if not isinstance(value, str) or not 16 <= len(value) <= 512 or not value.isascii() or any(c.isspace() for c in value):
            return error('INVALID_CREDENTIAL', 'قالب کلید نامعتبر است.', 422)
        try:
            if provider == 'openai':
                save_credential(guest, value)
            else:
                save_provider_credential(guest, provider, value)
        except CredentialUnavailable:
            return error('ENCRYPTION_UNAVAILABLE', 'ذخیره ممکن نیست؛ فایل کلید رمزنگاری سرور را تنظیم کنید.', 503)
        return self.get(request)

    @transaction.atomic
    def delete(self, request):
        guest = lock_guest(request)
        provider = self._provider(request)
        if provider not in {'openai', *SUPPORTED_PROVIDERS}:
            return error('PROVIDER_UNAVAILABLE', 'ارائه‌دهنده پشتیبانی نمی‌شود.', 422)
        row = active_credential(guest.id) if provider == 'openai' else active_provider_credential(guest.id, provider)
        if request.data.get('expected_revision') != (str(row.revision) if row else None):
            return error('STALE_CREDENTIAL', 'کلید تغییر کرده؛ وضعیت را تازه کنید.', 409)
        if provider == 'openai':
            from analysis.models import UserCredential
            invalidate_credential_operations(guest.id)
            UserCredential.objects.filter(guest_context=guest).delete()
        else:
            invalidate_provider_operations(guest.id, provider)
            ProviderCredential.objects.filter(guest_context=guest, provider=provider).delete()
        return Response(status=204)
