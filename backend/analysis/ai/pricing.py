import json
import math
from dataclasses import dataclass
from decimal import Decimal


# Standard, short-context prices verified against official OpenAI pricing on 2026-11-14.
# Cached-input discounts are intentionally ignored for a conservative reservation.
MODEL = "gpt-6-luna"
INPUT_USD_PER_MILLION = Decimal("0.10")
OUTPUT_USD_PER_MILLION = Decimal("0.50")
FRAMING_MARGIN_RATIO = Decimal("0.15")
MIN_FRAMING_MARGIN_TOKENS = 256


@dataclass(frozen=True)
class RequestCostEstimate:
    serialized_request_bytes: int
    conservative_input_tokens: int
    max_output_tokens: int
    per_attempt_microusd: int
    all_attempts_microusd: int


def _canonical_bytes(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def estimate_request_cost(*, instructions: str, input_json: str, schema: dict, max_output_tokens: int,
                          max_attempts: int, input_usd_per_million: Decimal = INPUT_USD_PER_MILLION,
                          output_usd_per_million: Decimal = OUTPUT_USD_PER_MILLION) -> RequestCostEstimate:
    """Bound the complete billable request without claiming tokenizer-exact accounting.

    UTF-8 bytes are treated as an intentionally loose token upper bound, then a framing margin is added for
    roles/boundaries that the provider counts but a local serializer cannot see.
    """
    serialized_bytes = (
        len(instructions.encode("utf-8"))
        + len(input_json.encode("utf-8"))
        + _canonical_bytes(schema)
    )
    margin = max(MIN_FRAMING_MARGIN_TOKENS, math.ceil(serialized_bytes * FRAMING_MARGIN_RATIO))
    input_tokens = serialized_bytes + margin
    per_attempt = math.ceil(
        Decimal(input_tokens) * input_usd_per_million
        + Decimal(max_output_tokens) * output_usd_per_million
    )
    return RequestCostEstimate(
        serialized_request_bytes=serialized_bytes,
        conservative_input_tokens=input_tokens,
        max_output_tokens=max_output_tokens,
        per_attempt_microusd=per_attempt,
        all_attempts_microusd=per_attempt * max_attempts,
    )


def observed_usage_cost_microusd(*, input_tokens: int, output_tokens: int,
                                 input_usd_per_million: Decimal = INPUT_USD_PER_MILLION,
                                 output_usd_per_million: Decimal = OUTPUT_USD_PER_MILLION) -> int:
    return math.ceil(
        Decimal(input_tokens) * input_usd_per_million
        + Decimal(output_tokens) * output_usd_per_million
    )
