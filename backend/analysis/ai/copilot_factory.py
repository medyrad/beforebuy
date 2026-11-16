"""Provider-neutral factory for the selected per-guest copilot provider."""
from base64 import b64encode

from django.conf import settings
from django.utils import timezone

from analysis.models import CopilotSettings, StreamOperation
from .openai_copilot import CopilotProviderError, ContextualFixtureGenerator, LimitedContextGenerator


def configured_copilot_generator(operation_id):
    from .copilot_context import manifest_is_current, pin_context
    if operation_id is None:
        if settings.COPILOT_AI_MODE == "mock":
            from analysis.conversation.streaming import FixtureGenerator
            return FixtureGenerator()
        raise CopilotProviderError("OPERATION_UNAVAILABLE")
    operation = StreamOperation.objects.select_related("conversation", "user_message").get(id=operation_id)
    bundle = pin_context(operation_id, operation.lease_owner)
    if bundle.limited_reason:
        if operation.conversation.openrouter_pilot:
            raise CopilotProviderError('INPUT_UNSUPPORTED')
        return LimitedContextGenerator()
    from analysis.conversation.replies import local_question
    if not operation.conversation.openrouter_pilot and local_question(bundle.provider_input.get('brief', {})):
        generator = ContextualFixtureGenerator(bundle.provider_input)
        generator.kind = 'DETERMINISTIC_CLARIFICATION'
        return generator
    if settings.COPILOT_AI_MODE == "mock" and not operation.conversation.openrouter_pilot:
        return ContextualFixtureGenerator(bundle.provider_input)

    preferences, _ = CopilotSettings.objects.get_or_create(
        guest_context_id=operation.conversation.guest_context_id)
    provider = preferences.provider
    from .provider_readiness import ensure_provider_live_eligible
    ensure_provider_live_eligible(provider)
    if provider != operation.credential_provider:
        raise CopilotProviderError("CREDENTIAL_PROVIDER_MISMATCH")
    guest_id = operation.conversation.guest_context_id
    lease_owner = operation.lease_owner

    def still_current():
        now = timezone.now()
        if provider in ("gapgpt", "openrouter"):
            from .provider_credentials import active_provider_credential
            row = active_provider_credential(guest_id, provider)
        else:
            from .credentials import active_credential
            row = active_credential(guest_id)
        return bool(
            row is not None and row.state == "VALIDATED" and row.revision == operation.credential_revision
            and StreamOperation.objects.filter(
                id=operation_id, status="RUNNING", lease_owner=lease_owner,
                lease_expires_at__gt=now, cancel_requested_at__isnull=True,
                conversation__expires_at__gt=now,
                conversation__brief_revision=operation.expected_brief_revision,
            ).exists()
            and manifest_is_current(operation_id, bundle.manifest, bundle.fingerprint)
        )

    if operation.user_message is None or not still_current():
        raise CopilotProviderError("CREDENTIAL_UNVALIDATED")
    if provider == 'openrouter':
        from .openrouter_copilot import OpenRouterCopilotGenerator, current_prices, sdk_events
        from .provider_credentials import decrypt_provider_credential
        if not operation.conversation.openrouter_pilot or not preferences.openrouter_data_consent:
            raise CopilotProviderError('SYNTHETIC_ONLY')
        context = dict(bundle.provider_input, choice=None, confirmed_memory=[], uploads=[])
        if bundle.provider_input.get('uploads'):
            raise CopilotProviderError('SYNTHETIC_ONLY')
        return OpenRouterCopilotGenerator(guest_id=guest_id, operation_id=operation_id, context=context,
            pricing=current_prices, transport=sdk_events,
            credential=lambda: decrypt_provider_credential(guest_id, provider, operation.credential_revision),
            still_current=still_current)
    if provider == "gapgpt":
        from .gapgpt_copilot import GapGPTCopilotGenerator, sdk_chat_events
        from .provider_credentials import decrypt_provider_credential
        return GapGPTCopilotGenerator(
            guest_id=guest_id, operation_id=operation_id, model=preferences.model,
            transport=sdk_chat_events,
            credential=lambda: decrypt_provider_credential(
                guest_id, provider, operation.credential_revision),
            still_current=still_current,
            operation_cap=settings.COPILOT_OPERATION_CAP_MICROUSD,
            session_cap=settings.COPILOT_SESSION_CAP_MICROUSD,
            daily_cap=settings.COPILOT_DAILY_CAP_MICROUSD,
            context=bundle.provider_input,
        )
    if provider == "openai":
        from .credentials import decrypt_current
        from .openai_copilot import OpenAICopilotGenerator, sdk_events
        images = [
            "data:" + image.media_type + ";base64," + b64encode(bytes(image.content)).decode("ascii")
            for image in operation.user_message.uploads.filter(expires_at__gt=timezone.now())
        ]
        return OpenAICopilotGenerator(
            guest_id=guest_id, operation_id=operation_id, model=preferences.model,
            transport=sdk_events,
            credential=lambda: decrypt_current(guest_id, operation.credential_revision),
            still_current=still_current,
            operation_cap=settings.COPILOT_OPERATION_CAP_MICROUSD,
            session_cap=settings.COPILOT_SESSION_CAP_MICROUSD,
            daily_cap=settings.COPILOT_DAILY_CAP_MICROUSD,
            context=bundle.provider_input, images=images,
        )
    raise CopilotProviderError("PROVIDER_UNAVAILABLE")
