from django.test import SimpleTestCase

from analysis.ai.evaluation import EVALUATION_CASES, EvaluationResult, assess_results


class EvaluationHarnessTests(SimpleTestCase):
    def test_dataset_is_versioned_and_covers_safety_edges(self):
        self.assertEqual(len(EVALUATION_CASES), 6)
        self.assertEqual({case.case_id for case in EVALUATION_CASES}, {f"EVAL-0{i}" for i in range(1, 7)})
        self.assertTrue(any(case.prompt_injection_label for case in EVALUATION_CASES))
        self.assertTrue(any(case.expected_unknown_ids for case in EVALUATION_CASES))

    def test_fixed_automatic_thresholds_fail_closed(self):
        results = [
            EvaluationResult(
                case_id=case.case_id,
                contract_valid=True,
                outcome_preserved=True,
                unknowns_preserved=True,
                forbidden_claims=0,
                latency_ms=100,
                estimated_cost_usd="0.0001",
            )
            for case in EVALUATION_CASES
        ]
        self.assertTrue(assess_results(results).automatic_pass)
        results[0] = EvaluationResult(**{**results[0].__dict__, "outcome_preserved": False})
        self.assertFalse(assess_results(results).automatic_pass)
