import json
import threading
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from analysis.ai.avalai_pricing import conservative_microusd_cap, estimate_cost_toman
from analysis.ai.evaluation import write_checkpoint_artifact
from analysis.ai.openai_adapter import (
    BudgetStateInconsistent,
    LiveBudgetLedger,
    OpenAIExplanationGenerator,
    ProviderResult,
    ProviderPermanentError,
    ProviderTransientError,
    ProviderUsage,
    LiveBudgetRejected,
)
from analysis.models import AIEvaluationAuthorization, AILiveBudgetWindow, AIInvocation, GuestContext
from tests.ai.test_openai_adapter import FakeTransport, explanation_request, valid_payload


class EvaluationBudgetAccountingTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))

    def ledger(self, **overrides):
        values = {
            "daily_budget_microusd": 10_000,
            "per_guest_daily_limit": 10,
            "circuit_threshold": 5,
            "circuit_cooldown_seconds": 300,
            "evaluation_authorization_id": "PDA-AI-EVAL-INITIAL-2026",
            "evaluation_authorized_toman": Decimal("100000"),
            "toman_per_usd": Decimal("100000"),
            "exchange_margin_ratio": Decimal("0.15"),
            "evaluation_run_id": "run-1",
            "evaluation_case_id": "EVAL-01",
        }
        values.update(overrides)
        return LiveBudgetLedger(**values)

    def test_evaluation_allowance_survives_restart_and_deployment_midnight_rollover(self):
        before_midnight = datetime(2026, 11, 14, 23, 59, tzinfo=datetime_timezone.utc)
        first_id, first_day = self.ledger().reserve(
            guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=1000, now=before_midnight,
        )
        self.ledger().settle(
            invocation_id=first_id, day=first_day, succeeded=True, attempts=1,
            attempt_usages=[ProviderUsage(1000, 0)], per_attempt_reserved_microusd=1000, latency_ms=1,
        )
        after_midnight = before_midnight + timedelta(minutes=2)
        self.ledger(evaluation_case_id="EVAL-02").reserve(
            guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=1000, now=after_midnight,
        )

        self.assertEqual(AILiveBudgetWindow.objects.count(), 2)
        authorization = AIEvaluationAuthorization.objects.get(pk="PDA-AI-EVAL-INITIAL-2026")
        self.assertGreater(authorization.spent_estimate_toman, 0)
        self.assertGreater(authorization.reserved_toman, 0)

    def test_retry_sums_known_usage_and_adds_allowance_only_for_unknown_attempt(self):
        transient = ProviderTransientError("timeout", usage=ProviderUsage(100, 10))
        transport = FakeTransport([
            transient,
            ProviderResult(json.dumps(valid_payload()), ProviderUsage(200, 20)),
        ])
        generator = OpenAIExplanationGenerator(
            transport=transport, guest_id=self.guest.id, daily_budget_microusd=10_000_000,
            sleeper=lambda _seconds: None,
        )
        estimate = generator.estimate(explanation_request())
        generator.generate(explanation_request())
        invocation = AIInvocation.objects.get()

        self.assertTrue(invocation.usage_complete)
        self.assertEqual(invocation.input_tokens, 300)
        self.assertEqual(invocation.output_tokens, 30)
        self.assertEqual(invocation.unknown_cost_microusd, 0)
        self.assertLess(invocation.estimated_cost_microusd, estimate.all_attempts_microusd)

    def test_timeout_unknown_and_malformed_known_usage_are_distinct(self):
        timeout_transport = FakeTransport([
            ProviderTransientError("timeout"),
            ProviderResult(json.dumps(valid_payload()), ProviderUsage(200, 20)),
        ])
        OpenAIExplanationGenerator(
            transport=timeout_transport, guest_id=self.guest.id, daily_budget_microusd=10_000_000,
            sleeper=lambda _seconds: None,
        ).generate(explanation_request())
        timeout_invocation = AIInvocation.objects.get()
        self.assertFalse(timeout_invocation.usage_complete)
        self.assertGreater(timeout_invocation.unknown_cost_microusd, 0)

        malformed_transport = FakeTransport([ProviderResult("not-json", ProviderUsage(50, 5))])
        generator = OpenAIExplanationGenerator(
            transport=malformed_transport, guest_id=self.guest.id, daily_budget_microusd=10_000_000,
            sleeper=lambda _seconds: None,
        )
        with self.assertRaises(ValueError):
            generator.generate(explanation_request())
        malformed = AIInvocation.objects.exclude(id=timeout_invocation.id).get()
        self.assertEqual(malformed.input_tokens, 50)
        self.assertEqual(malformed.output_tokens, 5)
        self.assertEqual(malformed.unknown_cost_microusd, 0)

    def test_incomplete_provider_response_preserves_billable_usage(self):
        transport = FakeTransport([
            ProviderPermanentError("empty_or_incomplete_response", usage=ProviderUsage(80, 8))
        ])
        generator = OpenAIExplanationGenerator(
            transport=transport, guest_id=self.guest.id, daily_budget_microusd=10_000_000,
            sleeper=lambda _seconds: None,
        )
        with self.assertRaises(ProviderPermanentError):
            generator.generate(explanation_request())
        invocation = AIInvocation.objects.get()
        self.assertEqual(invocation.input_tokens, 80)
        self.assertEqual(invocation.output_tokens, 8)
        self.assertEqual(invocation.unknown_cost_microusd, 0)

    def test_guest_cleanup_does_not_delete_sanitized_evaluation_invocation(self):
        ledger = self.ledger()
        invocation_id, _day = ledger.reserve(
            guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=100,
        )
        self.guest.delete()
        invocation = AIInvocation.objects.get(id=invocation_id)
        self.assertIsNone(invocation.guest_context_id)
        self.assertEqual(invocation.evaluation_case_id, "EVAL-01")

    def test_reserved_underflow_is_not_silently_clamped_and_recovery_is_idempotent(self):
        ledger = self.ledger(evaluation_authorization_id=None)
        invocation_id, day = ledger.reserve(
            guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=100,
        )
        AILiveBudgetWindow.objects.filter(day=day).update(reserved_cost_microusd=0)
        with self.assertRaises(BudgetStateInconsistent):
            ledger.recover(invocation_id=invocation_id)
        self.assertEqual(AIInvocation.objects.get(id=invocation_id).status, "reserved")

        AILiveBudgetWindow.objects.filter(day=day).update(reserved_cost_microusd=100)
        recovered = ledger.recover(invocation_id=invocation_id)
        again = ledger.recover(invocation_id=invocation_id)
        self.assertEqual(recovered.status, "failed")
        self.assertEqual(again.estimated_cost_microusd, 100)
        self.assertEqual(AILiveBudgetWindow.objects.get(day=day).spent_estimate_microusd, 100)

    def test_retry_observed_usage_overage_remains_visible(self):
        ledger = self.ledger(evaluation_authorization_id=None)
        invocation_id, day = ledger.reserve(
            guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=10,
        )
        invocation = ledger.settle(
            invocation_id=invocation_id, day=day, succeeded=True, attempts=2,
            attempt_usages=[ProviderUsage(1_000_000, 1_000_000), ProviderUsage(1_000_000, 1_000_000)],
            per_attempt_reserved_microusd=5, latency_ms=1,
        )
        self.assertGreater(invocation.estimated_cost_microusd, invocation.reserved_cost_microusd)
        self.assertEqual(invocation.unknown_cost_microusd, 0)
        self.assertTrue(invocation.usage_complete)


class EvaluationBudgetConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_evaluation_authorization_row_lock_allows_only_one_competing_reservation(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        AIEvaluationAuthorization.objects.create(
            id="PDA-AI-EVAL-INITIAL-2026", authorized_toman=Decimal("150")
        )
        barrier = threading.Barrier(2)
        outcomes = []

        def reserve(case_id):
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                ledger = LiveBudgetLedger(
                    daily_budget_microusd=10_000,
                    per_guest_daily_limit=10,
                    circuit_threshold=5,
                    circuit_cooldown_seconds=300,
                    evaluation_authorization_id="PDA-AI-EVAL-INITIAL-2026",
                    evaluation_authorized_toman=Decimal("150"),
                    toman_per_usd=Decimal("100000"),
                    exchange_margin_ratio=Decimal("0.15"),
                    evaluation_run_id="run-concurrent",
                    evaluation_case_id=case_id,
                )
                ledger.reserve(
                    guest_id=guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
                    schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=1000,
                )
                outcomes.append("reserved")
            except LiveBudgetRejected:
                outcomes.append("rejected")
            finally:
                close_old_connections()

        threads = [threading.Thread(target=reserve, args=(f"EVAL-0{index}",)) for index in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(sorted(outcomes), ["rejected", "reserved"])
        authorization = AIEvaluationAuthorization.objects.get(pk="PDA-AI-EVAL-INITIAL-2026")
        self.assertEqual(authorization.reserved_toman, Decimal("115.000000"))


class EvaluationCheckpointAndMoneyTests(TestCase):
    def test_checkpoint_is_incomplete_and_preserves_completed_and_remaining_cases(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            write_checkpoint_artifact(
                path,
                run_id="run-1",
                model="gpt-5.6-luna",
                prompt_version="PDA-EXPLAIN-P1",
                schema_version="PDA-EXPLAIN-v1",
                cases=[{"case_id": "EVAL-01", "status": "completed", "operation_id": "op-1"}],
                remaining_case_ids=["EVAL-02"],
                status="incomplete",
            )
            payload = json.loads(path.read_text())
            self.assertEqual(payload["status"], "incomplete")
            self.assertEqual(payload["last_completed_case_id"], "EVAL-01")
            self.assertEqual(payload["remaining_case_ids"], ["EVAL-02"])
            self.assertFalse(payload["raw_provider_transport_stored"])
            self.assertEqual(payload["evaluation_policy"]["historical_target_compatibility"], "incompatible")
            self.assertEqual(payload["evaluation_policy"]["current_product_cost_target_status"], "pending_product_decision")
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_non_finite_or_invalid_money_is_rejected(self):
        invalid = (Decimal("NaN"), Decimal("Infinity"), Decimal("-1"))
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    estimate_cost_toman(1, toman_per_usd=value)
                with self.assertRaises(ValueError):
                    conservative_microusd_cap(Decimal("100"), toman_per_usd=value)
