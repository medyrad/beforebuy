from django.test import SimpleTestCase

from analysis.ai.evaluation import EVALUATION_CASES, EvaluationResult, assess_results


class EvaluationHarnessTests(SimpleTestCase):
    def test_dataset_is_versioned_and_covers_safety_edges(self):
        self.assertEqual(len(EVALUATION_CASES), 7)
        self.assertEqual({case.case_id for case in EVALUATION_CASES}, {f"EVAL-0{i}" for i in range(1, 8)})
        self.assertTrue(any(case.prompt_injection_label for case in EVALUATION_CASES))
        self.assertTrue(any(case.expected_unknown_ids for case in EVALUATION_CASES))
        self.assertTrue(any(case.contradictory_input for case in EVALUATION_CASES))
        persian_digits = next(case for case in EVALUATION_CASES if case.case_id == "EVAL-02")
        self.assertEqual(persian_digits.data["price_toman"], "۲۰٬۰۰۰٬۰۰۰")
        self.assertTrue(all(case.expected_outcome_id for case in EVALUATION_CASES))

    def test_fixed_automatic_thresholds_fail_closed(self):
        results = [
            EvaluationResult(
                case_id=case.case_id,
                contract_valid=True,
                outcome_preserved=True,
                unknowns_preserved=True,
                semantic_support=None,
                readability=None,
                actionability=None,
                added_usefulness=None,
                attempts=1,
                input_tokens=100,
                output_tokens=20,
                latency_ms=100,
                reserved_cost_usd="0.0002",
                estimated_cost_usd="0.0001",
                cost_discrepancy_usd="-0.0001",
                usage_accounting="observed_single_attempt",
            )
            for case in EVALUATION_CASES
        ]
        assessment = assess_results(results)
        self.assertTrue(assessment.structural_pass)
        self.assertIsNone(assessment.overall_pass)
        self.assertFalse(assessment.human_review_complete)
        results[0] = EvaluationResult(**{**results[0].__dict__, "outcome_preserved": False})
        self.assertFalse(assess_results(results).structural_pass)
