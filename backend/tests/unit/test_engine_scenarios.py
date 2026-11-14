from django.test import SimpleTestCase

from analysis.domain import engine


def inputs(device, benefit, budget=25_000_000, price=20_000_000, target="NO_INFORMATION", tradeoffs=None):
    return {
        "product_label": "گوشی نمونه",
        "price_toman": price,
        "budget_toman": budget,
        "answers": {
            "Q-001": device,
            "Q-002": benefit,
            "Q-003": ["GENERAL_USE"],
            "Q-004": "FLEXIBLE",
            "Q-006": tradeoffs or ["NONE"],
            "F-003": target,
        },
    }


class AcceptedScenarioTests(SimpleTestCase):
    def analyze(self, data):
        self.assertTrue(hasattr(engine, "analyze"), "engine.analyze is not implemented")
        return engine.analyze(data)

    def test_unusable_essential_within_budget_keeps_target_unverified(self):
        result = self.analyze(inputs("UNUSABLE", "RESTORE_ESSENTIAL_ACCESS"))
        self.assertEqual(result.primary_outcome, "PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET")
        self.assertEqual(result.dimensions, {
            "budget": "WITHIN_BUDGET",
            "justification": "JUSTIFICATION_SUPPORTED",
            "target_fit": "TARGET_FIT_UNVERIFIED",
            "tradeoff": "NOT_REQUIRED",
        })
        self.assertEqual(result.matched_rule_ids, ["BUD-01", "JUS-04", "FIT-03", "TRD-03", "OUT-08"])

    def test_above_budget_precedes_supported_need_and_target_mismatch(self):
        data = inputs("UNUSABLE", "RESTORE_ESSENTIAL_ACCESS", budget=18_000_000, price=30_000_000,
                      target="USER_REPORTS_IT_DOES_NOT_FIT", tradeoffs=["REPAIR_CURRENT"])
        result = self.analyze(data)
        self.assertEqual(result.primary_outcome, "BUDGET_MISMATCH")
        self.assertEqual(result.dimensions["justification"], "JUSTIFICATION_SUPPORTED")
        self.assertEqual(result.dimensions["target_fit"], "USER_REPORTED_MISMATCH")
        self.assertIn("REPAIR_NOTED", result.actions)

    def test_missing_benefit_is_unknown_not_weak(self):
        result = self.analyze(inputs("SERIOUS_PROBLEM", "UNKNOWN"))
        self.assertEqual(result.dimensions["justification"], "JUSTIFICATION_UNKNOWN")
        self.assertEqual(result.primary_outcome, "INSUFFICIENT_CONTEXT")

    def test_no_device_enjoyment_remains_discretionary(self):
        result = self.analyze(inputs("NO_DEVICE", "PERSONAL_ENJOYMENT", tradeoffs=["ACCEPTED_TARGET_TRADEOFFS"]))
        self.assertEqual(result.dimensions["justification"], "DISCRETIONARY_CLEAR")
        self.assertEqual(result.primary_outcome, "DISCRETIONARY_CHOICE_WITHIN_BUDGET")

    def test_zero_and_unknown_budget_have_distinct_outcomes(self):
        zero = self.analyze(inputs("UNUSABLE", "RESTORE_ESSENTIAL_ACCESS", budget=0))
        unknown = self.analyze(inputs("UNUSABLE", "RESTORE_ESSENTIAL_ACCESS", budget=None))
        self.assertEqual(zero.primary_outcome, "BUDGET_MISMATCH")
        self.assertEqual(zero.budget_delta_toman, 20_000_000)
        self.assertEqual(unknown.primary_outcome, "PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN")
        self.assertIsNone(unknown.budget_delta_toman)

    def test_working_device_with_important_new_use_is_supported_but_target_unverified(self):
        result = self.analyze(inputs("WORKS_WELL", "ENABLE_IMPORTANT_NEW_USE"))
        self.assertEqual(result.dimensions["justification"], "JUSTIFICATION_SUPPORTED")
        self.assertEqual(result.dimensions["target_fit"], "TARGET_FIT_UNVERIFIED")
        self.assertEqual(result.primary_outcome, "PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET")

    def test_minor_problem_minor_benefit_needs_acknowledged_tradeoff(self):
        result = self.analyze(inputs(
            "MINOR_PROBLEM", "SOLVE_MINOR_LIMIT", tradeoffs=["ACCEPTED_TARGET_TRADEOFFS"]
        ))
        self.assertEqual(result.dimensions["justification"], "DISCRETIONARY_CLEAR")
        self.assertEqual(result.dimensions["tradeoff"], "ACKNOWLEDGED")
        self.assertEqual(result.primary_outcome, "DISCRETIONARY_CHOICE_WITHIN_BUDGET")

    def test_enjoyment_without_acknowledged_tradeoff_remains_inconclusive(self):
        result = self.analyze(inputs("WORKS_WELL", "PERSONAL_ENJOYMENT", tradeoffs=["UNKNOWN"]))
        self.assertEqual(result.dimensions["tradeoff"], "UNRESOLVED")
        self.assertEqual(result.primary_outcome, "INSUFFICIENT_CONTEXT")

    def test_unknown_budget_does_not_override_weak_or_contradictory_justification(self):
        weak = self.analyze(inputs("WORKS_WELL", "NO_CLEAR_BENEFIT", budget=None))
        contradictory = self.analyze(inputs("WORKS_WELL", "RESTORE_ESSENTIAL_ACCESS", budget=None))
        self.assertEqual(weak.primary_outcome, "RECONSIDER_OR_WAIT")
        self.assertEqual(contradictory.primary_outcome, "INSUFFICIENT_CONTEXT")
        self.assertEqual(weak.dimensions["budget"], "BUDGET_UNKNOWN")

    def test_user_reported_target_mismatch_precedes_otherwise_positive_result(self):
        result = self.analyze(inputs(
            "UNUSABLE", "RESTORE_ESSENTIAL_ACCESS", target="USER_REPORTS_IT_DOES_NOT_FIT"
        ))
        self.assertEqual(result.dimensions["target_fit"], "USER_REPORTED_MISMATCH")
        self.assertEqual(result.primary_outcome, "RECONSIDER_OR_WAIT")

    def test_evidence_has_source_and_allowed_attribution(self):
        result = self.analyze(inputs("UNUSABLE", "RESTORE_ESSENTIAL_ACCESS"))
        self.assertTrue(result.evidence)
        for item in result.evidence:
            self.assertIn(item["attribution"], {
                "USER_REPORTED", "DETERMINISTICALLY_DERIVED", "VERIFIED_EXTERNAL", "UNKNOWN"
            })
            self.assertTrue(item["source_id"])
