import json
import uuid
from decimal import Decimal
from unittest.mock import patch
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import AIEvaluationAuthorization, AILiveBudgetWindow, AIInvocation, GuestContext
from analysis.ai.avalai_adapter import AvalAICredit
from analysis.ai.evaluation import (
    EVALUATION_CASES, EvaluationResult, write_checkpoint_artifact, write_review_artifact,
)


class LiveEvaluationCommandGateTests(TestCase):
    def _run_pre_call_rejection(self, directory, *, deployment_budget="1"):
        output = StringIO()
        with patch.dict("os.environ", {"BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN": "100000"}, clear=False):
            with patch("analysis.management.commands.evaluate_live_ai.AvalAIAccountClient") as account:
                account.return_value.fetch_credit.return_value = AvalAICredit(
                    remaining_toman=Decimal("1000000"), toman_per_usd=Decimal("100000")
                )
                with override_settings(BEFOREBUY_AI_DAILY_BUDGET_TOMAN=Decimal(deployment_budget)):
                    call_command("evaluate_live_ai", artifact_dir=directory, stdout=output)
        payload = json.loads(output.getvalue())
        artifact = json.loads(Path(payload["artifact"]).read_text())
        return payload, artifact

    @override_settings(BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=False, AVALAI_API_KEY="not-used")
    def test_provider_eligibility_gate_prevents_any_live_invocation(self):
        with self.assertRaisesMessage(CommandError, "AvalAI eligibility is not confirmed"):
            call_command("evaluate_live_ai")
        self.assertEqual(AIInvocation.objects.count(), 0)

    def test_synthetic_review_artifact_remains_pending_without_human_scores(self):
        results = [EvaluationResult(
            case_id=case.case_id, contract_valid=True, outcome_preserved=True, unknowns_preserved=True,
            semantic_support=None, readability=None, actionability=None, added_usefulness=None,
            attempts=1, input_tokens=100, output_tokens=20, latency_ms=100, estimated_cost_usd="0.0001",
            reserved_cost_usd="0.0002", cost_discrepancy_usd="-0.0001",
            usage_accounting="observed_single_attempt",
        ) for case in EVALUATION_CASES]
        cases = [{
            "case_id": case.case_id, "synthetic_context": case.data, "deterministic_baseline": {},
            "rendered_ai_explanation": [],
            "human_review": {"semantic_support": None, "readability": None, "actionability": None,
                             "added_usefulness": None, "notes": None},
        } for case in EVALUATION_CASES]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            write_review_artifact(path, run_id="run-1", model="gpt-6-luna", prompt_version="PDA-EXPLAIN-P1",
                                  schema_version="PDA-EXPLAIN-v1", cases=cases, results=results)
            output = StringIO()
            call_command("assess_ai_review", str(path), stdout=output)
        self.assertIn('"human_review_complete": false', output.getvalue())
        self.assertIn('"overall_pass": null', output.getvalue())

    @override_settings(BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True, AVALAI_API_KEY="not-used")
    def test_evaluation_has_no_implicit_spending_budget(self):
        with patch.dict("os.environ", {}, clear=False):
            with patch("os.environ.get", side_effect=lambda key, default="": "" if key == "BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN" else default):
                with self.assertRaisesMessage(CommandError, "explicit valid toman budget"):
                    call_command("evaluate_live_ai")
        self.assertEqual(AIInvocation.objects.count(), 0)

    @override_settings(BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True, AVALAI_API_KEY="not-used")
    def test_evaluation_rejects_more_than_authorized_total_before_account_or_model_call(self):
        with patch.dict("os.environ", {"BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN": "100001"}, clear=False):
            with patch("analysis.management.commands.evaluate_live_ai.AvalAIAccountClient") as account:
                with self.assertRaisesMessage(CommandError, "exceeds the authorized 100000 toman total"):
                    call_command("evaluate_live_ai")
        account.assert_not_called()
        self.assertEqual(AIInvocation.objects.count(), 0)

    @override_settings(BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True, AVALAI_API_KEY="local-test-key")
    def test_deployment_budget_rejection_is_zero_call_incomplete_evidence_not_a_crash(self):
        with TemporaryDirectory() as directory:
            payload, artifact = self._run_pre_call_rejection(directory)
        self.assertEqual(payload["run_status"], "incomplete")
        self.assertEqual(artifact["cases"][0]["status"], "rejected")
        self.assertEqual(artifact["cases"][0]["attempts"], 0)
        self.assertEqual(artifact["cases"][0]["model_call_count"], 0)
        self.assertIn("deployment daily", artifact["cases"][0]["skip_reason"])
        self.assertEqual(AIInvocation.objects.count(), 0)

    @override_settings(BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True, AVALAI_API_KEY="local-test-key")
    def test_open_circuit_rejection_is_zero_call_incomplete_evidence(self):
        AILiveBudgetWindow.objects.create(
            day=timezone.now().date(), circuit_open_until=timezone.now() + timezone.timedelta(minutes=5)
        )
        with TemporaryDirectory() as directory:
            _payload, artifact = self._run_pre_call_rejection(directory, deployment_budget="100000")
        self.assertEqual(artifact["cases"][0]["status"], "rejected")
        self.assertIn("circuit", artifact["cases"][0]["skip_reason"])
        self.assertEqual(AIInvocation.objects.count(), 0)

    @override_settings(
        BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True,
        AVALAI_API_KEY="local-test-key",
        BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT=1,
    )
    def test_guest_quota_rejection_is_zero_call_incomplete_evidence(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        for _ in range(1):
            AIInvocation.objects.create(
                guest_context=guest, operation_id=uuid.uuid4(), provider="avalai", model="gpt-5.6-luna",
                prompt_version="PDA-EXPLAIN-P1", schema_version="PDA-EXPLAIN-v1", status="succeeded",
            )
        with TemporaryDirectory() as directory:
            with patch("analysis.management.commands.evaluate_live_ai.GuestContext.objects.create", return_value=guest):
                _payload, artifact = self._run_pre_call_rejection(directory, deployment_budget="100000")
        self.assertEqual(artifact["cases"][0]["status"], "rejected")
        self.assertIn("guest daily", artifact["cases"][0]["skip_reason"])
        self.assertEqual(AIInvocation.objects.filter(attempt_count__gt=0).count(), 0)

    @override_settings(
        BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True,
        AVALAI_API_KEY="local-test-key",
        BEFOREBUY_AI_DAILY_BUDGET_TOMAN=Decimal("100000"),
    )
    def test_resume_conservatively_recovers_outstanding_reservation_and_keeps_partial_evidence(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        authorization = AIEvaluationAuthorization.objects.create(
            id="PDA-AI-EVAL-INITIAL-2026", authorized_toman=Decimal("100000"),
            reserved_toman=Decimal("115"),
        )
        window = AILiveBudgetWindow.objects.create(
            day=timezone.now().date(), reserved_cost_microusd=1000,
            circuit_open_until=timezone.now() + timezone.timedelta(minutes=5),
        )
        operation_id = uuid.uuid4()
        invocation = AIInvocation.objects.create(
            guest_context=guest, operation_id=operation_id, provider="avalai", model="gpt-5.6-luna",
            prompt_version="PDA-EXPLAIN-P1", schema_version="PDA-EXPLAIN-v1", status="reserved",
            reserved_cost_microusd=1000, evaluation_authorization=authorization,
            evaluation_reserved_toman=Decimal("115"), evaluation_run_id="run-resume",
            evaluation_case_id="EVAL-01", exchange_rate_toman_per_usd=Decimal("100000"),
            exchange_margin_ratio=Decimal("0.15"),
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run-resume.json"
            write_checkpoint_artifact(
                path, run_id="run-resume", model="gpt-5.6-luna", prompt_version="PDA-EXPLAIN-P1",
                schema_version="PDA-EXPLAIN-v1",
                cases=[{"case_id": "EVAL-01", "status": "in_progress", "operation_id": str(operation_id)}],
                remaining_case_ids=[case.case_id for case in EVALUATION_CASES], status="incomplete",
            )
            output = StringIO()
            with patch.dict("os.environ", {"BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN": "100000"}, clear=False):
                with patch("analysis.management.commands.evaluate_live_ai.AvalAIAccountClient") as account:
                    account.return_value.fetch_credit.return_value = AvalAICredit(
                        remaining_toman=Decimal("1000000"), toman_per_usd=Decimal("100000")
                    )
                    call_command("evaluate_live_ai", resume_artifact=str(path), stdout=output)
            artifact = json.loads(path.read_text())

        invocation.refresh_from_db()
        authorization.refresh_from_db()
        window.refresh_from_db()
        self.assertEqual(invocation.status, "failed")
        self.assertEqual(invocation.error_class, "RecoveredStaleReservation")
        self.assertEqual(authorization.reserved_toman, Decimal("0"))
        self.assertEqual(authorization.spent_estimate_toman, Decimal("115"))
        self.assertEqual(window.reserved_cost_microusd, 0)
        self.assertEqual(artifact["cases"][0]["status"], "recovered_failed")
        self.assertTrue(artifact["cases"][0]["recovery_cost_is_conservative_not_invoice"])
        self.assertEqual(artifact["cases"][1]["status"], "rejected")
