from itertools import product

from django.test import SimpleTestCase

from analysis.domain import engine
from .test_engine_scenarios import inputs


class RubricInvariantTests(SimpleTestCase):
    def test_all_1134_categorical_inputs_have_exactly_one_status_per_dimension_and_outcome(self):
        self.assertTrue(hasattr(engine, "analyze"), "engine.analyze is not implemented")
        states = ["NO_DEVICE", "UNUSABLE", "SERIOUS_PROBLEM", "MINOR_PROBLEM", "WORKS_WELL", "UNKNOWN"]
        benefits = ["RESTORE_ESSENTIAL_ACCESS", "SOLVE_MAJOR_LIMIT", "ENABLE_IMPORTANT_NEW_USE",
                    "SOLVE_MINOR_LIMIT", "PERSONAL_ENJOYMENT", "NO_CLEAR_BENEFIT", "UNKNOWN"]
        budgets = [25_000_000, 0, None]
        targets = ["NO_INFORMATION", "USER_REPORTS_IT_FITS", "USER_REPORTS_IT_DOES_NOT_FIT"]
        trades = [["ACCEPTED_TARGET_TRADEOFFS"], ["NONE"], ["UNKNOWN"]]
        count = 0
        for state, benefit, budget, target, tradeoff in product(states, benefits, budgets, targets, trades):
            result = engine.analyze(inputs(state, benefit, budget=budget, target=target, tradeoffs=tradeoff))
            self.assertEqual(set(result.dimensions), {"budget", "justification", "target_fit", "tradeoff"})
            self.assertIsInstance(result.primary_outcome, str)
            self.assertTrue(result.primary_outcome)
            count += 1
        self.assertEqual(count, 1134)
