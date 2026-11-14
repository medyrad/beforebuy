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
    DATASET_VERSION, EVALUATION_CASES, EvaluationResult, assess_results, write_checkpoint_artifact,
)
from analysis.ai.generator import MockExplanationGenerator
from analysis.ai.avalai_adapter import AvalAIAccountClient, AvalAIExplanationGenerator
from analysis.ai.avalai_pricing import (
    conservative_microusd_cap, estimate_cost_toman, observed_avalai_usage_cost_microusd,
)
from analysis.ai.openai_adapter import (
    LiveBudgetLedger, PROMPT_VERSION, SCHEMA_VERSION,
)
from analysis.domain.engine import analyze
from analysis.models import AIEvaluationAuthorization, AIInvocation, GuestContext


class Command(BaseCommand):
    help = "Run the fixed synthetic live-AI evaluation and write a human-review artifact."

    def add_arguments(self, parser):
        parser.add_argument("--artifact-dir", default="artifacts/ai-evaluation")
        parser.add_argument("--resume-artifact")

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
        if not budget_toman.is_finite() or budget_toman <= 0:
            raise CommandError("live evaluation pending: explicit positive toman budget is required")
        if budget_toman > Decimal("100000"):
            raise CommandError("live evaluation cap exceeds the authorized 100000 toman total")

        try:
            deployment_budget_toman = Decimal(str(settings.BEFOREBUY_AI_DAILY_BUDGET_TOMAN))
            margin_ratio = Decimal(str(settings.BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO))
        except InvalidOperation as exc:
            raise CommandError(
                "live evaluation pending: deployment budget and margin must be valid decimals"
            ) from exc
        if (not deployment_budget_toman.is_finite() or deployment_budget_toman <= 0
                or not margin_ratio.is_finite() or margin_ratio < 0):
            raise CommandError("live evaluation pending: finite positive deployment budget and valid margin are required")

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
            margin_ratio=margin_ratio,
        )
        if budget_toman < required_toman:
            raise CommandError(
                f"explicit evaluation cap is below the conservative required reservation "
                f"({required_toman} toman)"
            )
        if credit.remaining_toman < required_toman:
            raise CommandError("live evaluation pending: existing AvalAI credit cannot cover the reservation")
        deployment_budget_microusd = conservative_microusd_cap(
            deployment_budget_toman,
            toman_per_usd=credit.toman_per_usd,
            margin_ratio=margin_ratio,
        )

        resume_path = Path(options["resume_artifact"]) if options.get("resume_artifact") else None
        artifact_cases = []
        if resume_path:
            try:
                previous = json.loads(resume_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise CommandError("resume artifact is unreadable") from exc
            if (previous.get("dataset") != DATASET_VERSION or previous.get("model") != settings.BEFOREBUY_AI_MODEL
                    or previous.get("status") == "completed"):
                raise CommandError("resume artifact is incompatible or already completed")
            run_id = previous["run_id"]
            artifact_cases = list(previous.get("cases", []))
            artifact_path = resume_path
        else:
            run_id = str(uuid.uuid4())
            artifact_path = Path(options["artifact_dir"]) / f"{run_id}.json"

        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        results = []

        def checkpoint(status="incomplete"):
            completed_ids = {item["case_id"] for item in artifact_cases if item.get("status") == "completed"}
            remaining = [case.case_id for case in EVALUATION_CASES if case.case_id not in completed_ids]
            authorization = AIEvaluationAuthorization.objects.filter(
                pk="PDA-AI-EVAL-INITIAL-2026"
            ).first()
            budget_evidence = None if authorization is None else {
                "authorization_id": authorization.id,
                "authorized_toman": str(authorization.authorized_toman),
                "reserved_toman": str(authorization.reserved_toman),
                "spent_estimate_toman": str(authorization.spent_estimate_toman),
                "within_authorization": (
                    authorization.reserved_toman + authorization.spent_estimate_toman
                    <= authorization.authorized_toman
                ),
                "estimate_is_not_provider_invoice": True,
            }
            write_checkpoint_artifact(
                artifact_path, run_id=run_id, model=settings.BEFOREBUY_AI_MODEL,
                prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION,
                cases=artifact_cases, remaining_case_ids=remaining, status=status,
                exchange_rate_toman_per_usd=str(credit.toman_per_usd),
                exchange_margin_ratio=str(margin_ratio),
                budget_evidence=budget_evidence,
            )

        completed_ids = {item["case_id"] for item in artifact_cases if item.get("status") == "completed"}
        if resume_path:
            recovery_ledger = LiveBudgetLedger(
                daily_budget_microusd=deployment_budget_microusd,
                per_guest_daily_limit=settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT,
                circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
                circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
                provider="avalai",
                usage_cost_calculator=observed_avalai_usage_cost_microusd,
            )
            for item in artifact_cases:
                if item.get("status") != "in_progress":
                    continue
                invocation = AIInvocation.objects.filter(operation_id=item.get("operation_id")).first()
                if invocation is not None and invocation.status == "reserved":
                    recovered = recovery_ledger.recover(invocation_id=invocation.id)
                    item.update({
                        "status": "recovered_failed",
                        "failure_status": recovered.error_class,
                        "attempts": recovered.attempt_count,
                        "usage_available": False,
                        "estimated_cost_usd": str(
                            Decimal(recovered.estimated_cost_microusd) / Decimal("1000000")
                        ),
                        "recovery_cost_is_conservative_not_invoice": True,
                    })
                elif invocation is None:
                    item.update({
                        "status": "interrupted_before_reservation",
                        "attempts": 0,
                        "model_call_count": 0,
                        "usage": None,
                    })
        for item in artifact_cases:
            if item.get("status") == "completed" and item.get("result"):
                results.append(EvaluationResult(**item["result"]))
        checkpoint()
        try:
            for case, data in normalized_cases:
                if case.case_id in completed_ids:
                    continue
                operation_id = uuid.uuid4()
                _baseline_result, baseline = services.build_report(data, generator=MockExplanationGenerator())
                case_record = {
                    "case_id": case.case_id,
                    "status": "in_progress",
                    "operation_id": str(operation_id),
                    "synthetic_context": data,
                    "deterministic_baseline": baseline,
                    "rendered_ai_explanation": [],
                    "human_review": {
                        "semantic_support": None, "readability": None, "actionability": None,
                        "added_usefulness": None, "notes": None,
                    },
                }
                artifact_cases.append(case_record)
                checkpoint()
                generator = AvalAIExplanationGenerator.from_api_key(
                    settings.AVALAI_API_KEY, guest_id=guest.id, operation_id=operation_id,
                    model=settings.BEFOREBUY_AI_MODEL, timeout_seconds=settings.BEFOREBUY_AI_TIMEOUT_SECONDS,
                    max_attempts=settings.BEFOREBUY_AI_MAX_ATTEMPTS,
                    max_input_bytes=settings.BEFOREBUY_AI_MAX_INPUT_BYTES,
                    max_output_tokens=settings.BEFOREBUY_AI_MAX_OUTPUT_TOKENS,
                    daily_budget_microusd=deployment_budget_microusd,
                    per_guest_daily_limit=settings.BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT,
                    circuit_threshold=settings.BEFOREBUY_AI_CIRCUIT_THRESHOLD,
                    circuit_cooldown_seconds=settings.BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS,
                    evaluation_authorization_id="PDA-AI-EVAL-INITIAL-2026",
                    evaluation_authorized_toman=Decimal("100000"),
                    toman_per_usd=credit.toman_per_usd,
                    exchange_margin_ratio=margin_ratio,
                    evaluation_run_id=run_id,
                    evaluation_case_id=case.case_id,
                )
                _deterministic, report = services.build_report(data, generator=generator)
                invocation = AIInvocation.objects.filter(operation_id=operation_id).first()
                if invocation is None:
                    case_record.update({
                        "status": "rejected",
                        "skip_reason": generator.last_rejection_reason or "pre_call_rejection",
                        "attempts": 0,
                        "model_call_count": 0,
                        "usage": None,
                        "estimated_cost_usd": "0",
                    })
                    checkpoint()
                    break
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
                        "observed_all_attempts" if invocation.usage_complete else "mixed_known_and_conservative_unknown"
                    ),
                )
                if invocation.status == "succeeded" and contract_valid:
                    results.append(result)
                deterministic_count = len(baseline["explanation_blocks"])
                case_record.update({
                    "status": "completed" if invocation.status == "succeeded" and contract_valid else "failed",
                    "provider": invocation.provider,
                    "model": invocation.model,
                    "pricing_version": "AVALAI-2026-11-14",
                    "attempts": invocation.attempt_count,
                    "usage_available": invocation.input_tokens is not None,
                    "request_id": invocation.provider_request_id,
                    "failure_status": invocation.error_class,
                    "rendered_ai_explanation": report["explanation_blocks"][deterministic_count:],
                    "result": result.__dict__,
                })
                checkpoint()
                if case_record["status"] != "completed":
                    break
            authorization = AIEvaluationAuthorization.objects.filter(
                pk="PDA-AI-EVAL-INITIAL-2026"
            ).first()
            spend_pass = None if authorization is None else (
                authorization.reserved_toman + authorization.spent_estimate_toman
                <= authorization.authorized_toman
            )
            assessment = assess_results(results, total_spend_pass=spend_pass)
            run_completed = len(results) == len(EVALUATION_CASES)
            checkpoint("completed" if run_completed else "incomplete")
            self.stdout.write(json.dumps({
                "dataset": DATASET_VERSION, "run_id": run_id, "model": settings.BEFOREBUY_AI_MODEL,
                "structural_pass": assessment.structural_pass,
                "operational_pass": assessment.operational_pass,
                "latency_pass": assessment.latency_pass,
                "product_cost_target_pass": assessment.product_cost_target_pass,
                "historical_product_cost_target_compatibility": "incompatible",
                "total_spend_pass": assessment.total_spend_pass,
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
                    margin_ratio=margin_ratio,
                )),
                "provider_exchange_rate_irt_per_unit": str(credit.toman_per_usd),
                "authorized_total_cap_toman": str(budget_toman),
                "provider_cost_is_estimate_not_invoice": True,
                "run_status": "completed" if run_completed else "incomplete",
                "artifact": str(artifact_path), "raw_payloads_logged": False,
                "note": "sample_upper_latency_ms is the upper end of this tiny sample, not a production p95 estimate",
            }, sort_keys=True))
        finally:
            checkpoint("completed" if len(results) == len(EVALUATION_CASES) else "incomplete")
            guest.delete()
