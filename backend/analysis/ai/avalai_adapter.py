import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .avalai_pricing import (
    MODEL,
    estimate_avalai_request_cost,
    observed_avalai_usage_cost_microusd,
)
from .openai_adapter import (
    MissingCredentials,
    OpenAIExplanationGenerator,
    ProviderPermanentError,
    ProviderResult,
    ProviderTransientError,
    ProviderUsage,
)


PROVIDER = "avalai"
BASE_URL = "https://api.avalai.ir/v1"
USER_CREDIT_URL = "https://api.avalai.ir/user/v1/credit"


def _cost_toman(response) -> Decimal | None:
    value = getattr(response, "estimated_cost", None)
    if value is None:
        value = getattr(response, "model_extra", {}).get("estimated_cost")
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict) or value.get("irt") is None:
        return None
    try:
        parsed = Decimal(str(value["irt"]))
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() and parsed >= 0 else None


class AvalAIResponsesTransport:
    def __init__(self, api_key: str, *, client=None):
        if not api_key:
            raise MissingCredentials("AVALAI_API_KEY is not configured")
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=BASE_URL, max_retries=0)
        self.client = client

    def create(self, **kwargs) -> ProviderResult:
        try:
            raw = self.client.responses.with_raw_response.create(
                model=kwargs["model"],
                instructions=kwargs["instructions"],
                input=kwargs["input_json"],
                text={"format": kwargs["schema"]},
                max_output_tokens=kwargs["max_output_tokens"],
                store=kwargs["store"],
                timeout=kwargs["timeout"],
            )
            response = raw.parse()
        except Exception as exc:
            try:
                from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
            except ImportError:
                raise ProviderPermanentError("provider_sdk_unavailable") from exc
            if isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError)):
                raise ProviderTransientError(type(exc).__name__) from exc
            if isinstance(exc, APIStatusError) and exc.status_code in {408, 409, 429, 500, 502, 503, 504}:
                raise ProviderTransientError(f"http_{exc.status_code}") from exc
            raise ProviderPermanentError(type(exc).__name__) from exc

        usage = getattr(response, "usage", None)
        parsed_usage = None if usage is None else ProviderUsage(
            input_tokens=int(getattr(usage, "input_tokens", 0)),
            output_tokens=int(getattr(usage, "output_tokens", 0)),
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise ProviderPermanentError(
                "empty_or_incomplete_response",
                usage=parsed_usage,
                request_id=raw.headers.get("avalai-request-id"),
                provider_estimated_cost_toman=_cost_toman(response),
            )
        return ProviderResult(
            output_text=output_text,
            usage=parsed_usage,
            request_id=raw.headers.get("avalai-request-id"),
            provider_estimated_cost_toman=_cost_toman(response),
        )


@dataclass(frozen=True)
class AvalAICredit:
    remaining_toman: Decimal
    toman_per_usd: Decimal


class AvalAIAccountClient:
    def __init__(self, api_key: str, *, timeout_seconds: float = 8):
        if not api_key:
            raise MissingCredentials("AVALAI_API_KEY is not configured")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def fetch_credit(self) -> AvalAICredit:
        request = Request(USER_CREDIT_URL, headers={"Authorization": f"Bearer {self.api_key}"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            remaining = Decimal(str(payload["remaining_irt"]))
            exchange_rate = Decimal(str(payload["exchange_rate"]))
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError, InvalidOperation) as exc:
            raise ProviderPermanentError("avalai_credit_check_failed") from exc
        if (not remaining.is_finite() or not exchange_rate.is_finite()
                or remaining < 0 or exchange_rate <= 0):
            raise ProviderPermanentError("avalai_credit_response_invalid")
        return AvalAICredit(remaining_toman=remaining, toman_per_usd=exchange_rate)


class AvalAIExplanationGenerator(OpenAIExplanationGenerator):
    provider = PROVIDER
    default_model = MODEL

    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            request_cost_estimator=estimate_avalai_request_cost,
            usage_cost_calculator=observed_avalai_usage_cost_microusd,
        )

    @classmethod
    def from_api_key(cls, api_key: str, **kwargs):
        return cls(transport=AvalAIResponsesTransport(api_key), **kwargs)


__all__ = [
    "AvalAIAccountClient",
    "AvalAICredit",
    "AvalAIExplanationGenerator",
    "AvalAIResponsesTransport",
    "ProviderResult",
    "ProviderUsage",
]
