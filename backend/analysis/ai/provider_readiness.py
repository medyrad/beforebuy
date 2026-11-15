"""Fail-closed activation checks shared by API acceptance and provider factories."""
from django.conf import settings

from .openai_copilot import CopilotProviderError


def ensure_provider_live_eligible(provider):
    if provider == "openai":
        from .openai_copilot import ensure_live_eligible
        ensure_live_eligible()
        return
    if provider != "gapgpt":
        raise CopilotProviderError("PROVIDER_UNAVAILABLE")
    if not settings.COPILOT_PHASE12_SPENDING_AUTHORIZED:
        raise CopilotProviderError("SPENDING_AUTHORIZATION_REQUIRED")
    if not all(type(value) is int and value > 0 for value in (
        settings.COPILOT_USD_TO_TOMAN_RATE,
        settings.COPILOT_PHASE12_TOTAL_CAP_TOMAN,
        settings.COPILOT_OPERATION_CAP_MICROUSD,
        settings.COPILOT_SESSION_CAP_MICROUSD,
        settings.COPILOT_DAILY_CAP_MICROUSD,
    )):
        raise CopilotProviderError("CONFIGURATION_MISSING")
    if not settings.COPILOT_EXCHANGE_MARGIN_RATIO.is_finite() or settings.COPILOT_EXCHANGE_MARGIN_RATIO < 0:
        raise CopilotProviderError("CONFIGURATION_MISSING")
