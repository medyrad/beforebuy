from decimal import Decimal, ROUND_FLOOR

from .pricing import estimate_request_cost, observed_usage_cost_microusd


MODEL = "gpt-5.6-luna"
INPUT_USD_PER_MILLION = Decimal("5.00")
CACHED_INPUT_USD_PER_MILLION = Decimal("0.50")
OUTPUT_USD_PER_MILLION = Decimal("30.00")
DEFAULT_EXCHANGE_MARGIN_RATIO = Decimal("0.15")


def estimate_avalai_request_cost(**kwargs):
    return estimate_request_cost(
        **kwargs,
        input_usd_per_million=INPUT_USD_PER_MILLION,
        output_usd_per_million=OUTPUT_USD_PER_MILLION,
    )


def observed_avalai_usage_cost_microusd(*, input_tokens: int, output_tokens: int) -> int:
    return observed_usage_cost_microusd(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_usd_per_million=INPUT_USD_PER_MILLION,
        output_usd_per_million=OUTPUT_USD_PER_MILLION,
    )


def estimate_cost_toman(microusd: int, *, toman_per_usd: Decimal,
                        margin_ratio: Decimal = DEFAULT_EXCHANGE_MARGIN_RATIO) -> Decimal:
    if (microusd < 0 or not toman_per_usd.is_finite() or not margin_ratio.is_finite()
            or toman_per_usd <= 0 or margin_ratio < 0):
        raise ValueError("cost conversion values must be non-negative and rate must be positive")
    return (
        Decimal(microusd) / Decimal("1000000") * toman_per_usd * (Decimal("1") + margin_ratio)
    ).quantize(Decimal("0.000001"))


def conservative_microusd_cap(cap_toman: Decimal, *, toman_per_usd: Decimal,
                              margin_ratio: Decimal = DEFAULT_EXCHANGE_MARGIN_RATIO) -> int:
    if (not cap_toman.is_finite() or not toman_per_usd.is_finite() or not margin_ratio.is_finite()
            or cap_toman <= 0 or toman_per_usd <= 0 or margin_ratio < 0):
        raise ValueError("cap and rate must be positive and margin non-negative")
    value = cap_toman * Decimal("1000000") / (toman_per_usd * (Decimal("1") + margin_ratio))
    return int(value.to_integral_value(rounding=ROUND_FLOOR))
