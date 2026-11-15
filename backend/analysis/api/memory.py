from copy import deepcopy
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response
from analysis.guest import get_or_create_guest, extend_guest_session_for_eligible_action
from analysis.models import GuestContext, CopilotSettings, StreamOperation
from analysis.memory.service import preferences, consent, scope_for, validate_criterion, serialize, propose
from .base import ObjectBodyAPIView
from .conversations import active_conversation, error
from .errors import CopilotUnavailable
from analysis.conversation.serializers import serialize_brief


def lock_guest(request):
    guest = get_or_create_guest(request)
    return GuestContext.objects.select_for_update().get(id=guest.id)


def stale(data, revision):
    return type(data.get('expected_revision')) is not int or data['expected_revision'] != revision


class CopilotSettingsView(ObjectBodyAPIView):
    def get(self, request):
        item, _ = CopilotSettings.objects.get_or_create(guest_context=get_or_create_guest(request))
        from analysis.ai.provider_catalog import catalog_for
        from analysis.ai.provider_credentials import active_provider_credential
        from analysis.ai.credentials import active_credential
        credential = active_credential(item.guest_context_id) if item.provider == 'openai' else active_provider_credential(
            item.guest_context_id, item.provider)
        connection = 'NOT_CONFIGURED' if credential is None else credential.state
        if item.provider == 'openai':
            connection = 'VALIDATION_BLOCKED' if credential else connection
        mode = 'DEMONSTRATION' if settings.COPILOT_AI_MODE == 'mock' else 'BLOCKED'
        if settings.COPILOT_AI_MODE != 'mock' and connection == 'VALIDATED':
            from analysis.ai.openai_copilot import CopilotProviderError
            from analysis.ai.provider_readiness import ensure_provider_live_eligible
            try:
                ensure_provider_live_eligible(item.provider)
                mode = 'LIVE_READY'
            except CopilotProviderError:
                pass
        return Response({'memory_enabled': item.memory_enabled, 'provider': item.provider,
                         'model': item.model, 'revision': item.revision,
                         'mode': mode,
                         'credential_state': 'NOT_CONFIGURED' if credential is None else credential.state,
                         'connection': connection, 'catalog': catalog_for(item.provider, item.model)})

    @transaction.atomic
    def patch(self, request):
        guest = lock_guest(request)
        item, _ = CopilotSettings.objects.get_or_create(guest_context=guest)
        if stale(request.data, item.revision):
            return error('STALE_SETTINGS', 'تنظیمات تغییر کرده؛ صفحه را تازه کنید.', 409)
        if 'memory_enabled' in request.data:
            if type(request.data['memory_enabled']) is not bool:
                return error('VALIDATION_ERROR', 'گزینهٔ حافظه نامعتبر است.', 422)
            item.memory_enabled = request.data['memory_enabled']
        if 'provider' in request.data:
            from analysis.ai.provider_catalog import CATALOGS, DEFAULT_MODELS
            provider = request.data['provider']
            if not isinstance(provider, str) or provider not in CATALOGS:
                return error('PROVIDER_UNAVAILABLE', 'ارائه‌دهنده پشتیبانی نمی‌شود.', 422)
            if provider != item.provider:
                item.provider = provider
                item.model = DEFAULT_MODELS[provider]
        if 'model' in request.data:
            from analysis.ai.provider_catalog import CATALOGS
            if not isinstance(request.data['model'], str) or request.data['model'] not in CATALOGS[item.provider]:
                return error('MODEL_UNAVAILABLE', 'مدل پشتیبانی نمی‌شود.', 422)
            item.model = request.data['model']
        item.revision += 1
        item.save()
        return self.get(request)


class CopilotModelsRefreshView(ObjectBodyAPIView):
    def post(self, request):
        from analysis.ai.provider_credentials import active_provider_credential, decrypt_provider_credential
        from analysis.ai.credentials import CredentialUnavailable, active_credential, decrypt_current
        from analysis.ai.openai_copilot import (
            CopilotProviderError, ensure_live_eligible, sdk_model_ids,
        )
        from analysis.ai.copilot_catalog import discover_models
        from analysis.ai.openai_adapter import ProviderTransientError
        guest = get_or_create_guest(request)
        preferences, _ = CopilotSettings.objects.get_or_create(guest_context=guest)
        if preferences.provider == 'gapgpt':
            credential = active_provider_credential(guest.id, 'gapgpt')
            if credential is None:
                return error('CREDENTIAL_UNVALIDATED', 'ابتدا کلید GapGPT را ذخیره کنید.', 409)
            from analysis.ai.openai_copilot import CopilotProviderError
            from analysis.ai.provider_readiness import ensure_provider_live_eligible
            try:
                ensure_provider_live_eligible('gapgpt')
            except CopilotProviderError as exc:
                return error(str(exc), 'اعتبارسنجی GapGPT یک فراخوانی مولد کم‌حجم است و مجوز هزینهٔ Phase 12 کامل نیست.', 409)
            # GapGPT documents no free model-list/auth probe. This explicit action therefore makes one
            # bounded, ledger-accounted generation through the same adapter and exact selected model.
            import uuid
            from analysis.ai.gapgpt_copilot import GapGPTCopilotGenerator, sdk_chat_events
            context = {
                'current_message': 'اعتبارسنجی صریح اتصال؛ فقط یک پرسش کوتاه و طبیعی بپرس.',
                'brief': {}, 'history': {'items': [], 'omitted_count': 0, 'truncated': False},
                'choice': None, 'confirmed_memory': [], 'uploads': [],
            }
            adapter = GapGPTCopilotGenerator(
                guest_id=guest.id, operation_id=uuid.uuid4(), model=preferences.model,
                transport=sdk_chat_events,
                credential=lambda: decrypt_provider_credential(guest.id, 'gapgpt', credential.revision),
                still_current=lambda: bool(
                    (current := active_provider_credential(guest.id, 'gapgpt')) is not None
                    and current.revision == credential.revision),
                operation_cap=settings.COPILOT_OPERATION_CAP_MICROUSD,
                session_cap=settings.COPILOT_SESSION_CAP_MICROUSD,
                daily_cap=settings.COPILOT_DAILY_CAP_MICROUSD, context=context,
            )
            try:
                list(adapter.generate())
            except CredentialUnavailable:
                return error('CREDENTIAL_UNAVAILABLE', 'کلید ذخیره‌شده قابل استفاده نیست.', 409)
            except CopilotProviderError as exc:
                code = str(exc)
                if code in {'PROVIDER_REJECTED', 'MALFORMED_OUTPUT', 'TRANSIENT_EXHAUSTED', 'PROVIDER_FAILED'}:
                    type(credential).objects.filter(id=credential.id, revision=credential.revision).update(
                        state='VALIDATION_FAILED')
                if code not in {'BUDGET_REJECTED', 'SESSION_COST_LIMIT', 'OPERATION_COST_LIMIT',
                                'STALE_OPERATION', 'PROVIDER_REJECTED', 'MALFORMED_OUTPUT',
                                'TRANSIENT_EXHAUSTED', 'PROVIDER_FAILED'}:
                    code = 'PROVIDER_REJECTED'
                return error(code, 'اعتبارسنجی صریح اتصال موفق نبود.', 409)
            updated = type(credential).objects.filter(
                id=credential.id, revision=credential.revision, state='STORED_UNVALIDATED').update(state='VALIDATED')
            if updated != 1:
                return error('STALE_CREDENTIAL', 'کلید در زمان اعتبارسنجی تغییر کرد.', 409)
            from analysis.ai.provider_catalog import catalog_for
            catalog = deepcopy(catalog_for('gapgpt', preferences.model))
            catalog['source'] = 'EXPLICIT_BILLABLE_VALIDATION'
            catalog['saved_status'] = 'AVAILABLE'
            return Response(catalog)
        try:
            ensure_live_eligible()
        except CopilotProviderError:
            return error('REGION_BLOCKED', 'فهرست حساب در منطقهٔ فعلی قابل بازیابی نیست.', 409)
        credential = active_credential(guest.id)
        if credential is None or credential.state != 'VALIDATED':
            return error('CREDENTIAL_UNVALIDATED', 'ابتدا اتصال را به‌طور صریح تأیید کنید.', 409)
        try:
            account_ids = sdk_model_ids(key=decrypt_current(guest.id, credential.revision))
        except CredentialUnavailable:
            return error('CREDENTIAL_UNAVAILABLE', 'کلید ذخیره‌شده قابل استفاده نیست.', 409)
        except ProviderTransientError:
            return error('PROVIDER_UNAVAILABLE', 'بازیابی فهرست حساب موقتاً ممکن نیست.', 503)
        except CopilotProviderError:
            return error('PROVIDER_REJECTED', 'ارائه‌دهنده درخواست فهرست حساب را نپذیرفت.', 409)
        response = Response(discover_models(account_ids, saved_model=preferences.model))
        response['Cache-Control'] = 'private, no-store'
        return response


class MemoryListView(ObjectBodyAPIView):
    def get(self, request):
        response = Response({'items': [serialize(i) for i in preferences(get_or_create_guest(request))]})
        response['Cache-Control'] = 'private, no-store'
        return response

    @transaction.atomic
    def delete(self, request):
        guest = lock_guest(request)
        guest.preferences.all().delete()
        return Response(status=204)


class MemoryDetailView(ObjectBodyAPIView):
    @transaction.atomic
    def patch(self, request, memory_id):
        guest = lock_guest(request)
        item = preferences(guest).select_for_update().filter(id=memory_id).first()
        if item is None:
            raise CopilotUnavailable
        if stale(request.data, item.revision):
            return error('STALE_MEMORY', 'ترجیح تغییر کرده؛ دوباره بررسی کنید.', 409)
        if not consent(guest):
            return error('MEMORY_DISABLED', 'ابتدا حافظه را فعال کنید.', 409)
        if 'criterion' in request.data:
            criterion = validate_criterion(item.category, request.data['criterion'])
            if criterion['scope'] != item.criterion['scope'] or criterion['field'] != item.criterion['field']:
                return error('VALIDATION_ERROR', 'مخاطب و ویژگی ترجیح قابل انتقال نیست.', 422)
            item.criterion = criterion
        state = request.data.get('state', item.state)
        if state not in ('CONFIRMED', 'REJECTED', 'CANDIDATE') or (item.confirmed_at and state == 'CANDIDATE'):
            return error('VALIDATION_ERROR', 'وضعیت ترجیح نامعتبر است.', 422)
        if state == 'CONFIRMED' and item.confirmed_at is None:
            item.confirmed_at = timezone.now()
            item.expires_at = min(guest.access_expires_at, item.source_conversation.expires_at,
                item.confirmed_at + timedelta(days=settings.COPILOT_MEMORY_CONFIRMED_DAYS))
        item.state = state
        item.revision += 1
        item.save()
        return Response(serialize(item))

    @transaction.atomic
    def delete(self, request, memory_id):
        item = preferences(lock_guest(request)).filter(id=memory_id).first()
        if item is None:
            raise CopilotUnavailable
        item.delete()
        return Response(status=204)


class MemoryExportView(ObjectBodyAPIView):
    def get(self, request):
        response = Response({'items': [serialize(i) for i in preferences(get_or_create_guest(request))]})
        response['Cache-Control'] = 'private, no-store'
        response['Content-Disposition'] = 'attachment; filename="beforebuy-preferences.json"'
        return response


class ConversationMemoryView(ObjectBodyAPIView):
    def get(self, request, conversation_id):
        guest = get_or_create_guest(request)
        c = active_conversation(guest, conversation_id)
        items = [] if c.temporary or not consent(guest) else [serialize(i) for i in preferences(guest).filter(
            state='CONFIRMED', category=c.brief.category) if i.criterion['scope'] == scope_for(c.brief)]
        return Response({'items': items})

    @transaction.atomic
    def post(self, request, conversation_id):
        guest = lock_guest(request)
        c = active_conversation(guest, conversation_id, lock=True)
        if c.temporary or not consent(guest):
            return error('MEMORY_DISABLED', 'این گفت‌وگو از حافظه استفاده نمی‌کند.', 409)
        if stale(request.data, c.brief_revision) or not c.brief.confirmed:
            return error('STALE_BRIEF_REVISION', 'ابتدا نیاز جاری را تأیید کنید.', 409)
        return Response({'items': [serialize(i) for i in propose(guest, c)]}, status=201)

    @transaction.atomic
    def patch(self, request, conversation_id):
        guest = lock_guest(request)
        c = active_conversation(guest, conversation_id, lock=True)
        if c.temporary or not consent(guest):
            return error('MEMORY_DISABLED', 'این گفت‌وگو از حافظه استفاده نمی‌کند.', 409)
        if stale(request.data, c.brief_revision) or c.brief.confirmed:
            return error('STALE_BRIEF_REVISION', 'حافظه فقط به نیاز تأییدنشده افزوده می‌شود.', 409)
        import uuid
        try:
            memory_id = uuid.UUID(str(request.data.get('memory_id')))
        except ValueError:
            raise CopilotUnavailable
        item = preferences(guest).select_for_update().filter(id=memory_id, state='CONFIRMED', category=c.brief.category).first()
        if item is None or item.criterion['scope'] != scope_for(c.brief):
            raise CopilotUnavailable
        if type(request.data.get('memory_revision')) is not int or request.data['memory_revision'] != item.revision:
            return error('STALE_MEMORY', 'ترجیح ذخیره‌شده تغییر کرده است.', 409)
        brief = c.brief
        profile = deepcopy(brief.comparison)
        criteria = profile.setdefault('criteria', [])
        if not any(i['field'] == item.criterion['field'] for i in criteria):
            criteria.append(deepcopy(item.criterion))
            brief.comparison = profile
            brief.revision += 1
            # Receipt of the explicit application action, not a dangling reference to erasable memory.
            brief.provenance = [*brief.provenance, {'field': 'comparison', 'source_type': 'CONFIRMED_MEMORY', 'source_id': str(uuid.uuid4())}]
            brief.save()
            c.brief_revision = brief.revision
            c.generation_epoch += 1
            c.last_eligible_activity_at = timezone.now()
            c.expires_at = c.last_eligible_activity_at + timedelta(days=90)
            c.save()
            StreamOperation.objects.filter(conversation=c, status__in=['PENDING', 'RUNNING']).update(cancel_requested_at=timezone.now())
            extend_guest_session_for_eligible_action(request, c.expires_at)
        return Response(serialize_brief(brief))
