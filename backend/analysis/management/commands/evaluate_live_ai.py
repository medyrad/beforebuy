import json
import math
import os
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analysis import services
from analysis.ai.evaluation import EVALUATION_CASES, EvaluationResult, assess_results
from analysis.ai.openai_adapter import OpenAIExplanationGenerator
from analysis.models import AIInvocation, GuestContext


class Command(BaseCommand):
    help = "Run the fixed M3 live-AI evaluation without printing or persisting raw prompts/responses."

    def handle(self, *args, **options):
        if not settings.BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED:
            raise CommandError("live evaluation pending: supported backend/user region is not confirmed")
        if not settings.OPENAI_API_KEY:
            raise CommandError("live evaluation pending: OPENAI_API_KEY is not configured")
        raw_budget = os.environ.get("BEFOREBUY_LIVE_EVAL_BUDGET_USD", "")
        try:
            budget_usd = Decimal(raw_budget)
        except InvalidOperation as exc:
            raise CommandError("live evaluation pending: explicit valid dollar budget is required") from exc
        if budget_usd <= 0:
            raise CommandError("live evaluation pending: explicit positive dollar budget is required")

        per_attempt_microusd = math.ceil(
            settings.BEFOREBUY_AI_MAX_INPUT_BYTES * Decimal("0.10")
            + settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS * Decimal("0.50")
        )
        required_reservation = per_attempt_microusd * settings.BEFOREBUY_AI_MAX_ATTEMPTS * len(EVALUATION_CASES)
        budget_microusd = int(budget_usd * Decimal("1000000"))
        if budget_microusd < required_reservation:
            raise CommandError(
                f"explicit evaluation cap is below the conservative required reservation "
                f"({required_reservation / 1_000_000:.6f} USD)"
            )

        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        results = []
        try:
            for case in EVALUATION_CASES:
                operation_id = uuid.uuid4()
                generator = OpenAIExplanationGenerator.from_api_key(
                    settings.OPENAI_API_KEY,
                    guest_id=guest.id,
                    operation_id=operation_id,
                    model=settings.BEFOREBUY_AI_MODEL,
                    timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
                    max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
                    max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
                    max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
                    daily_budget_microusd=min(settings.BEFOREBUY_AI_DAILY_BUDGET_MICROUSD, budget_microusd),
                    per_guest_daily_limit=max(settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT, len(EVALUATION_CASES)),
                    circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
                    circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
                )
                _deterministic, report = services.build_report(case.data, generator=generator)
                invocation = AIInvocation.objects.get(operation_id=operation_id)
                valid = report["mode"] == "AI_ASSISTED_SUCCESS"
                results.append(EvaluationResult(
                    case_id=case.case_id,
                    contract_valid=valid,
                    outcome_preserved=valid,
                    unknowns_preserved=valid and tuple(report["unknowns"]) == case.expected_unknown_ids,
                    forbidden_claims=0 if valid else 1,
                    latency_ms=invocation.latency_ms or 0,
                    estimated_cost_usd=str(Decimal(invocation.estimated_cost_microusd) / Decimal("1000000")),
                ))
            assessment = assess_results(results)
            self.stdout.write(json.dumps({
                "dataset": "PDA-AI-EVAL-v1",
                "model": settings.BEFOREBUY_AI_MODEL,
                "automatic_pass": assessment.automatic_pass,
                "case_count": assessment.case_count,
                "p95_latency_ms": assessment.p95_latency_ms,
                "average_cost_usd": assessment.average_cost_usd,
                "human_review_required": True,
                "raw_payloads_logged": False,
            }, sort_keys=True))
        finally:
            guest.delete()
