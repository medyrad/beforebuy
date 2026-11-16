"""Explicit synthetic validation, distinct from credential storage and legal eligibility."""
import uuid
from django.db import transaction
from rest_framework.response import Response
from analysis.models import CopilotSettings, Conversation, GuestContext
from analysis.ai.credentials import CredentialUnavailable
from analysis.ai.openai_copilot import CopilotProviderError
from analysis.ai.provider_credentials import active_provider_credential, decrypt_provider_credential
from analysis.ai.provider_catalog import catalog_for, OPENROUTER_MODEL
from .conversations import error


def start_pilot(request, guest, preferences):
    if request.data.get('synthetic_consent') is not True:
        return error('SYNTHETIC_CONSENT_REQUIRED', 'این آزمایش فقط برای متن ساختگی است؛ رضایت پردازش داده را جداگانه تأیید کنید.', 409)
    from analysis.ai.openrouter_copilot import ensure_eligible, OpenRouterCopilotGenerator, current_prices, sdk_events
    try:
        ensure_eligible()
    except CopilotProviderError as exc:
        return error(str(exc), 'صلاحیت خدمت و مسیر Baidu برای کاربران و استقرار ایران هنوز مستند و تأیید نشده است؛ رضایت داده جایگزین آن نیست.', 409)
    credential = active_provider_credential(guest.id, 'openrouter')
    if credential is None:
        return error('CREDENTIAL_UNVALIDATED', 'ابتدا کلید OpenRouter را در همین تنظیمات ذخیره کنید.', 409)

    def current():
        row = active_provider_credential(guest.id, 'openrouter')
        return bool(row and row.revision == credential.revision and CopilotSettings.objects.filter(
            guest_context=guest, provider='openrouter', model=OPENROUTER_MODEL, revision=preferences.revision).exists())

    adapter = OpenRouterCopilotGenerator(guest_id=guest.id, operation_id=uuid.uuid4(),
        credential=lambda: decrypt_provider_credential(guest.id, 'openrouter', credential.revision),
        still_current=current, pricing=current_prices, transport=sdk_events,
        context={'current_message': 'گوشی من شکسته، می‌خواهم آیفون ده بخرم.', 'brief': {},
                 'history': {'items': [], 'omitted_count': 0, 'truncated': False},
                 'choice': None, 'confirmed_memory': [], 'uploads': []})
    try:
        list(adapter.generate())
    except CredentialUnavailable:
        return error('CREDENTIAL_UNAVAILABLE', 'کلید رمز‌شده قابل بارگذاری نیست.', 409)
    except CopilotProviderError as exc:
        if str(exc) in {'OPENROUTER_AUTH_FAILED', 'OPENROUTER_ACCESS_DENIED', 'OPENROUTER_CREDIT_REQUIRED'}:
            type(credential).objects.filter(id=credential.id, revision=credential.revision).update(state='VALIDATION_FAILED')
        return error(str(exc), 'آزمایش رایگان تأیید نشد؛ درخواست خودکار تکرار نمی‌شود. کد خطا: ' + str(exc), 409)
    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        if not current():
            return error('STALE_CREDENTIAL', 'کلید یا ارائه‌دهنده هنگام آزمایش تغییر کرد.', 409)
        type(credential).objects.filter(id=credential.id, revision=credential.revision).update(state='VALIDATED')
        CopilotSettings.objects.filter(guest_context=guest).update(openrouter_data_consent=True)
        conversation = Conversation.objects.create_for_guest(guest, title='آزمایش ساختگی OpenRouter')
        conversation.temporary = conversation.openrouter_pilot = True
        conversation.save(update_fields=['temporary', 'openrouter_pilot'])
    return Response({**catalog_for('openrouter', OPENROUTER_MODEL),
                     'source': 'EXPLICIT_SYNTHETIC_VALIDATION', 'saved_status': 'AVAILABLE',
                     'conversation_id': str(conversation.id)})
