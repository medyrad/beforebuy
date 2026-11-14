from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from analysis.models import AIInvocation


class LiveEvaluationCommandGateTests(TestCase):
    @override_settings(BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED=False, OPENAI_API_KEY="not-used")
    def test_region_gate_prevents_any_live_invocation(self):
        with self.assertRaisesMessage(CommandError, "region is not confirmed"):
            call_command("evaluate_live_ai")
        self.assertEqual(AIInvocation.objects.count(), 0)

    @override_settings(BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED=True, OPENAI_API_KEY="not-used")
    def test_evaluation_has_no_implicit_spending_budget(self):
        with patch.dict("os.environ", {}, clear=False):
            with patch("os.environ.get", side_effect=lambda key, default="": "" if key == "BEFOREBUY_LIVE_EVAL_BUDGET_USD" else default):
                with self.assertRaisesMessage(CommandError, "explicit valid dollar budget"):
                    call_command("evaluate_live_ai")
        self.assertEqual(AIInvocation.objects.count(), 0)
