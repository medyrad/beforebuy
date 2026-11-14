import json
import threading
import uuid
from datetime import timedelta

from django.db import close_old_connections
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from analysis.ai.openai_adapter import (
    LiveBudgetLedger,
    LiveBudgetRejected,
    OpenAIExplanationGenerator,
    ProviderResult,
    ProviderTransientError,
    ProviderUsage,
)
from analysis.models import AILiveBudgetWindow, AIInvocation, GuestContext
from tests.ai.test_openai_adapter import FakeTransport, explanation_request, valid_payload
from analysis.ai.factory import UnavailableLiveExplanationGenerator, configured_explanation_generator
from analysis.ai.generator import MockExplanationGenerator


class LiveBudgetControlTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))

    def generator(self, transport, **overrides):
        values = {
            "transport": transport,
            "guest_id": self.guest.id,
            "operation_id": uuid.uuid4(),
            "daily_budget_microusd": 1_000_000,
            "per_guest_daily_limit": 10,
            "sleeper": lambda _seconds: None,
        }
        values.update(overrides)
        return OpenAIExplanationGenerator(**values)

    def test_success_reserves_and_settles_without_storing_payload(self):
        transport = FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(100, 20))])
        self.generator(transport).generate(explanation_request(target_label="برچسب خصوصی"))

        invocation = AIInvocation.objects.get()
        window = AILiveBudgetWindow.objects.get()
        self.assertEqual(invocation.status, "succeeded")
        self.assertEqual(invocation.attempt_count, 1)
        self.assertEqual(invocation.input_tokens, 100)
        self.assertGreater(invocation.estimated_cost_microusd, 0)
        self.assertEqual(window.reserved_cost_microusd, 0)
        self.assertGreater(window.spent_estimate_microusd, 0)
        stored = repr(invocation.__dict__)
        self.assertNotIn("برچسب خصوصی", stored)
        self.assertNotIn("headline_fa", stored)

    def test_observed_usage_is_not_clipped_and_repeated_settlement_is_idempotent(self):
        ledger = LiveBudgetLedger(daily_budget_microusd=1_000_000, per_guest_daily_limit=10,
                                  circuit_threshold=5, circuit_cooldown_seconds=300)
        invocation_id, day = ledger.reserve(guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
                                            schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=10)
        usage = ProviderUsage(1_000_000, 1_000_000)
        ledger.settle(invocation_id=invocation_id, day=day, succeeded=True, attempts=1, usage=usage, latency_ms=10)
        first = AILiveBudgetWindow.objects.get().spent_estimate_microusd
        ledger.settle(invocation_id=invocation_id, day=day, succeeded=True, attempts=1, usage=usage, latency_ms=10)
        invocation = AIInvocation.objects.get(id=invocation_id)
        window = AILiveBudgetWindow.objects.get()
        self.assertGreater(invocation.estimated_cost_microusd, invocation.reserved_cost_microusd)
        self.assertEqual(window.spent_estimate_microusd, first)
        self.assertEqual(window.reserved_cost_microusd, 0)
        restrictive = LiveBudgetLedger(daily_budget_microusd=100, per_guest_daily_limit=10,
                                       circuit_threshold=5, circuit_cooldown_seconds=300)
        with self.assertRaises(LiveBudgetRejected):
            restrictive.reserve(guest_id=self.guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
                                schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=1)

    def test_retry_with_unknown_total_usage_settles_conservatively(self):
        transport = FakeTransport([
            ProviderTransientError("timeout"),
            ProviderResult(json.dumps(valid_payload()), ProviderUsage(10, 10)),
        ])
        self.generator(transport).generate(explanation_request())
        invocation = AIInvocation.objects.get()
        self.assertEqual(invocation.attempt_count, 2)
        self.assertFalse(invocation.usage_complete)
        self.assertGreater(invocation.known_cost_microusd, 0)
        self.assertGreater(invocation.unknown_cost_microusd, 0)
        self.assertEqual(
            invocation.estimated_cost_microusd,
            invocation.known_cost_microusd + invocation.unknown_cost_microusd,
        )
        self.assertLess(invocation.estimated_cost_microusd, invocation.reserved_cost_microusd)

    @override_settings(BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT=1)
    def test_per_guest_limit_rejects_without_provider_call(self):
        first = FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(10, 10))])
        self.generator(first, per_guest_daily_limit=1).generate(explanation_request())
        blocked = FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(10, 10))])
        with self.assertRaises(LiveBudgetRejected):
            self.generator(blocked, per_guest_daily_limit=1).generate(explanation_request())
        self.assertEqual(blocked.calls, [])

    def test_spending_limit_rejects_before_provider_call(self):
        transport = FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(10, 10))])
        with self.assertRaises(LiveBudgetRejected):
            self.generator(transport, daily_budget_microusd=1).generate(explanation_request())
        self.assertEqual(transport.calls, [])

    def test_five_provider_failures_open_shared_circuit(self):
        for _ in range(5):
            transport = FakeTransport([ProviderTransientError("timeout"), ProviderTransientError("timeout")])
            with self.assertRaises(ProviderTransientError):
                self.generator(transport).generate(explanation_request())
        blocked = FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(10, 10))])
        with self.assertRaises(LiveBudgetRejected):
            self.generator(blocked).generate(explanation_request())
        self.assertEqual(blocked.calls, [])
        self.assertGreater(AILiveBudgetWindow.objects.get().circuit_open_until, timezone.now())

    @override_settings(BEFOREBUY_AI_MODE="mock")
    def test_mock_mode_never_selects_live_adapter(self):
        request = RequestFactory().get("/")
        self.assertIsInstance(configured_explanation_generator(request, self.guest), MockExplanationGenerator)

    @override_settings(
        BEFOREBUY_AI_MODE="live",
        BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED=True,
        OPENAI_API_KEY="",
    )
    def test_live_mode_without_credentials_selects_fail_closed_fallback_path(self):
        request = RequestFactory().get("/")
        self.assertIsInstance(
            configured_explanation_generator(request, self.guest), UnavailableLiveExplanationGenerator
        )


class LiveBudgetConcurrencyTests(TransactionTestCase):
    def test_row_locked_window_allows_only_one_competing_reservation(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        barrier = threading.Barrier(2)
        results = []

        def reserve():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                ledger = LiveBudgetLedger(daily_budget_microusd=1_000, per_guest_daily_limit=10,
                                          circuit_threshold=5, circuit_cooldown_seconds=300)
                ledger.reserve(guest_id=guest.id, operation_id=uuid.uuid4(), model="gpt-6-luna",
                               schema_version="PDA-EXPLAIN-v1", reserved_cost_microusd=600)
                results.append("reserved")
            except LiveBudgetRejected:
                results.append("rejected")
            finally:
                close_old_connections()

        threads = [threading.Thread(target=reserve) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(sorted(results), ["rejected", "reserved"])
        self.assertEqual(AILiveBudgetWindow.objects.get().reserved_cost_microusd, 600)
