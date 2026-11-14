from django.conf import settings

from .generator import E2ELimitedExplanationGenerator, MockExplanationGenerator
from .openai_adapter import MissingCredentials, OpenAIExplanationGenerator


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
    if not settings.BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED:
        return UnavailableLiveExplanationGenerator("supported deployment/user region is not confirmed")
    if not settings.OPENAI_API_KEY:
        return UnavailableLiveExplanationGenerator("OPENAI_API_KEY is not configured")
    return OpenAIExplanationGenerator.from_api_key(
        settings.OPENAI_API_KEY,
        guest_id=guest.id,
        model=settings.BEFOREBUY_AI_MODEL,
        timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
        max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
        max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
        max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
        daily_budget_microusd=settings.BEFOREBUY_AI_DAILY_BUDGET_MICROUSD,
        per_guest_daily_limit=settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT,
        circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
        circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
    )
