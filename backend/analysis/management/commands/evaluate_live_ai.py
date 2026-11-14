import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analysis import services
from analysis.ai.evaluation import (
    DATASET_VERSION, EVALUATION_CASES, EvaluationResult, assess_results, write_review_artifact,
)
from analysis.ai.generator import MockExplanationGenerator
from analysis.ai.avalai_adapter import AvalAIAccountClient, AvalAIExplanationGenerator
from analysis.ai.avalai_pricing import conservative_microusd_cap, estimate_cost_toman
from analysis.ai.openai_adapter import (
    PROMPT_VERSION, SCHEMA_VERSION,
)
from analysis.domain.engine import analyze
from analysis.models import AIInvocation, GuestContext


class Command(BaseCommand):
    help = "Run the fixed synthetic live-AI evaluation and write a human-review artifact."

    def add_arguments(self, parser):
        parser.add_argument("--artifact-dir", default="artifacts/ai-evaluation")

    def handle(self, *args, **options):
        if not settings.BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED:
            raise CommandError("live evaluation pending: AvalAI eligibility is not confirmed")
        if not settings.AVALAI_API_KEY:
            raise CommandError("live evaluation pending: AVALAI_API_KEY is not configured")
        raw_budget = os.environ.get("BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN", "")
        try:
            budget_toman = Decimal(raw_budget)
        except InvalidOperation as exc:
            raise CommandError("live evaluation pending: explicit valid toman budget is required") from exc
        if budget_toman <= 0:
            raise CommandError("live evaluation pending: explicit positive toman budget is required")
        if budget_toman > Decimal("100000"):
            raise CommandError("live evaluation cap exceeds the authorized 100000 toman total")

        credit = AvalAIAccountClient(
            settings.AVALAI_API_KEY, timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS
        ).fetch_credit()

        normalized_cases = [(case, services.normalize_input(case.data)) for case in EVALUATION_CASES]
        preflight = AvalAIExplanationGenerator(
            transport=None, model=settings.BEFOREBUY_AI_MODEL,
            timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
            max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
            max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
            max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
        )
        required_reservation = 0
        for _case, data in normalized_cases:
            deterministic = analyze(data)
            estimate = preflight.estimate(
                services.build_explanation_request(data, deterministic)
            )
            if estimate.conservative_input_tokens > settings.BEFOREBUY_AI_MAX_INPUT_BYTES:
                raise CommandError("synthetic evaluation case exceeds the complete request bound")
            required_reservation += estimate.all_attempts_microusd
        required_toman = estimate_cost_toman(
            required_reservation,
            toman_per_usd=credit.toman_per_usd,
            margin_ratio=settings.BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO,
        )
        if budget_toman < required_toman:
            raise CommandError(
                f"explicit evaluation cap is below the conservative required reservation "
                f"({required_toman} toman)"
            )
        if credit.remaining_toman < required_toman:
            raise CommandError("live evaluation pending: existing AvalAI credit cannot cover the reservation")
        budget_microusd = conservative_microusd_cap(
            budget_toman,
            toman_per_usd=credit.toman_per_usd,
            margin_ratio=settings.BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO,
        )

        run_id = str(uuid.uuid4())
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        results, artifact_cases = [], []
        try:
            for case, data in normalized_cases:
                operation_id = uuid.uuid4()
                _baseline_result, baseline = services.build_report(data, generator=MockExplanationGenerator())
                generator = AvalAIExplanationGenerator.from_api_key(
                    settings.AVALAI_API_KEY, guest_id=guest.id, operation_id=operation_id,
                    model=settings.BEFOREBUY_AI_MODEL, timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
                    max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
                    max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
                    max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
                    daily_budget_microusd=budget_microusd,
                    per_guest_daily_limit=max(settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT, len(EVALUATION_CASES)),
                    circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
                    circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
                )
                _deterministic, report = services.build_report(data, generator=generator)
                invocation = AIInvocation.objects.get(operation_id=operation_id)
                contract_valid = report["mode"] == "AI_ASSISTED_SUCCESS"
                result = EvaluationResult(
                    case_id=case.case_id,
                    contract_valid=contract_valid,
                    outcome_preserved=report["primary_outcome"] == case.expected_outcome_id,
                    unknowns_preserved=tuple(report["unknowns"]) == case.expected_unknown_ids,
                    semantic_support=None, readability=None, actionability=None, added_usefulness=None,
                    attempts=invocation.attempt_count, input_tokens=invocation.input_tokens,
                    output_tokens=invocation.output_tokens, latency_ms=invocation.latency_ms or 0,
                    reserved_cost_usd=str(Decimal(invocation.reserved_cost_microusd) / Decimal("1000000")),
                    estimated_cost_usd=str(Decimal(invocation.estimated_cost_microusd) / Decimal("1000000")),
                    cost_discrepancy_usd=str(
                        Decimal(invocation.estimated_cost_microusd - invocation.reserved_cost_microusd)
                        / Decimal("1000000")
                    ),
                    usage_accounting=(
                        "observed_single_attempt"
                        if invocation.attempt_count == 1 and invocation.input_tokens is not None
                        else "conservative_reservation"
                    ),
                )
                results.append(result)
                deterministic_count = len(baseline["explanation_blocks"])
                artifact_cases.append({
                    "case_id": case.case_id,
                    "synthetic_context": data,
                    "deterministic_baseline": baseline,
                    "rendered_ai_explanation": report["explanation_blocks"][deterministic_count:],
                    "human_review": {
                        "semantic_support": None, "readability": None, "actionability": None,
                        "added_usefulness": None, "notes": None,
                    },
                })
            assessment = assess_results(results)
            artifact_path = Path(options["artifact_dir"]) / f"{run_id}.json"
            write_review_artifact(
                artifact_path, run_id=run_id, model=settings.BEFOREBUY_AI_MODEL,
                prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION,
                cases=artifact_cases, results=results,
            )
            self.stdout.write(json.dumps({
                "dataset": DATASET_VERSION, "run_id": run_id, "model": settings.BEFOREBUY_AI_MODEL,
                "structural_pass": assessment.structural_pass,
                "operational_pass": assessment.operational_pass,
                "human_review_complete": assessment.human_review_complete,
                "overall_pass": assessment.overall_pass,
                "case_count": assessment.case_count,
                "sample_upper_latency_ms": assessment.sample_upper_latency_ms,
                "average_cost_usd": assessment.average_cost_usd,
                "total_attempts": sum(item.attempts for item in results),
                "total_input_tokens": sum(item.input_tokens or 0 for item in results),
                "total_output_tokens": sum(item.output_tokens or 0 for item in results),
                "total_estimated_cost_usd": str(sum(Decimal(item.estimated_cost_usd) for item in results)),
                "total_estimated_cost_toman_with_margin": str(estimate_cost_toman(
                    sum(int(Decimal(item.estimated_cost_usd) * Decimal("1000000")) for item in results),
                    toman_per_usd=credit.toman_per_usd,
                    margin_ratio=settings.BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO,
                )),
                "provider_exchange_rate_irt_per_unit": str(credit.toman_per_usd),
                "authorized_total_cap_toman": str(budget_toman),
                "provider_cost_is_estimate_not_invoice": True,
                "artifact": str(artifact_path), "raw_payloads_logged": False,
                "note": "sample_upper_latency_ms is the upper end of this tiny sample, not a production p95 estimate",
            }, sort_keys=True))
        finally:
            guest.delete()
