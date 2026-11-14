from unittest.mock import patch
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from analysis.models import AIInvocation
from analysis.ai.evaluation import EVALUATION_CASES, EvaluationResult, write_review_artifact


class LiveEvaluationCommandGateTests(TestCase):
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
