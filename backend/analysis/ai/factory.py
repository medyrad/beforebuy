from django.conf import settings
from decimal import Decimal

from .avalai_adapter import AvalAIExplanationGenerator
from .avalai_pricing import conservative_microusd_cap
from .generator import E2ELimitedExplanationGenerator, MockExplanationGenerator
from .openai_adapter import MissingCredentials


class UnavailableLiveExplanationGenerator:
    def __init__(self, reason: str):
        self.reason = reason

    def generate(self, request):
        raise MissingCredentials(self.reason)


def configured_explanation_generator(request, guest):
    if (
        settings.BEFOREBUY_E2E_TEST_CONTROLS
        and request.headers.get("X-BeforeBuy-E2E-Explanation") == "limited"
    ):
        return E2ELimitedExplanationGenerator()
    if settings.BEFOREBUY_AI_MODE != "live":
        return MockExplanationGenerator()
    if settings.BEFOREBUY_AI_PROVIDER != "avalai":
        return UnavailableLiveExplanationGenerator("only the approved AvalAI provider may be selected")
    if not settings.BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED:
        return UnavailableLiveExplanationGenerator("AvalAI eligibility is not confirmed")
    if not settings.AVALAI_API_KEY:
        return UnavailableLiveExplanationGenerator("AVALAI_API_KEY is not configured")
    toman_rate = Decimal(str(settings.BEFOREBUY_AI_USD_TO_TOMAN_RATE))
    daily_budget_toman = Decimal(str(settings.BEFOREBUY_AI_DAILY_BUDGET_TOMAN))
    if toman_rate <= 0 or daily_budget_toman <= 0:
        return UnavailableLiveExplanationGenerator("AvalAI rate and toman deployment budget are not configured")
    daily_budget_microusd = conservative_microusd_cap(
        daily_budget_toman,
        toman_per_usd=toman_rate,
        margin_ratio=Decimal(str(settings.BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO)),
    )
    return AvalAIExplanationGenerator.from_api_key(
        settings.AVALAI_API_KEY,
        guest_id=guest.id,
        model=settings.BEFOREBUY_AI_MODEL,
        timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
        max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
        max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
        max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
        daily_budget_microusd=daily_budget_microusd,
        per_guest_daily_limit=settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT,
        circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
        circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
    )
