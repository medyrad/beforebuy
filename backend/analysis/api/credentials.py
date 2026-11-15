from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.response import Response
from analysis.guest import get_or_create_guest
from analysis.ai.credentials import active_credential, save_credential, keyring, CredentialUnavailable, invalidate_credential_operations
from .base import ObjectBodyAPIView
from .memory import lock_guest
from .conversations import error


@method_decorator(sensitive_post_parameters('key'), name='dispatch')
class CredentialView(ObjectBodyAPIView):
    def get(self, request):
        row = active_credential(get_or_create_guest(request).id)
        try:
            keyring()
            encryption_available = True
        except CredentialUnavailable:
            encryption_available = False
        response = Response({'state': row.state if row else 'NOT_CONFIGURED', 'masked': '••••••••' if row else None,
            'revision': str(row.revision) if row else None, 'expires_at': row.expires_at.isoformat() if row else None,
            'encryption_available': encryption_available, 'validation': 'UNAVAILABLE_BLOCKED'})
        response['Cache-Control'] = 'private, no-store'
        return response

    @transaction.atomic
    def put(self, request):
        guest = lock_guest(request)
        row = active_credential(guest.id)
        if request.data.get('expected_revision') != (str(row.revision) if row else None):
            return error('STALE_CREDENTIAL', 'کلید تغییر کرده؛ وضعیت را تازه کنید.', 409)
        value = request.data.get('key')
        if not isinstance(value, str) or not 16 <= len(value) <= 512 or not value.isascii() or any(c.isspace() for c in value):
            return error('INVALID_CREDENTIAL', 'قالب کلید نامعتبر است.', 422)
        try:
            save_credential(guest, value)
        except CredentialUnavailable:
            return error('ENCRYPTION_UNAVAILABLE', 'ذخیره ممکن نیست؛ فایل کلید رمزنگاری سرور را تنظیم کنید.', 503)
        return self.get(request)

    @transaction.atomic
    def delete(self, request):
        guest = lock_guest(request)
        row = active_credential(guest.id)
        if request.data.get('expected_revision') != (str(row.revision) if row else None):
            return error('STALE_CREDENTIAL', 'کلید تغییر کرده؛ وضعیت را تازه کنید.', 409)
        from analysis.models import UserCredential
        invalidate_credential_operations(guest.id)
        UserCredential.objects.filter(guest_context=guest).delete()
        return Response(status=204)
