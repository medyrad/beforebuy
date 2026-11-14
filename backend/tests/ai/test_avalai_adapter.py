import json
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from analysis.ai.avalai_adapter import (
    AvalAIExplanationGenerator,
    AvalAIResponsesTransport,
    ProviderResult,
    ProviderUsage,
)
from analysis.ai.avalai_pricing import (
    conservative_microusd_cap,
    estimate_cost_toman,
    observed_avalai_usage_cost_microusd,
)
from analysis.ai.factory import UnavailableLiveExplanationGenerator, configured_explanation_generator
from analysis.models import AIInvocation, GuestContext
from tests.ai.test_openai_adapter import FakeTransport, explanation_request, valid_payload


class _FakeResponse:
    output_text = json.dumps(valid_payload(), ensure_ascii=False)
    usage = type("Usage", (), {"input_tokens": 120, "output_tokens": 30})()
    estimated_cost = {"irt": "12.50", "unit": "0.00010000", "exchange_rate": 125_000}


class _FakeRawResponse:
    headers = {"avalai-request-id": "req-avalai-1"}

    def parse(self):
        return _FakeResponse()


class _FakeResponses:
    def __init__(self):
        self.calls = []
        self.with_raw_response = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeRawResponse()


class _FakeClient:
    def __init__(self):
        self.responses = _FakeResponses()


class AvalAIAdapterContractTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(
            access_expires_at=timezone.now() + timezone.timedelta(days=1)
        )

    def test_documented_responses_protocol_and_metadata_are_consumed(self):
        client = _FakeClient()
        transport = AvalAIResponsesTransport("local-test-key", client=client)

        result = transport.create(
            model="gpt-5.6-luna",
            instructions="system",
            input_json="{}",
            schema={"type": "json_schema"},
            max_output_tokens=512,
            store=False,
            timeout=8,
        )

        call = client.responses.calls[0]
        self.assertEqual(call["model"], "gpt-5.6-luna")
        self.assertEqual(call["text"], {"format": {"type": "json_schema"}})
        self.assertFalse(call["store"])
        self.assertEqual(result.usage, ProviderUsage(120, 30))
        self.assertEqual(result.request_id, "req-avalai-1")
        self.assertEqual(result.provider_estimated_cost_toman, Decimal("12.50"))

    def test_selected_tariff_and_toman_conversion_include_exchange_margin(self):
        generator = AvalAIExplanationGenerator(
            transport=FakeTransport([ProviderResult(json.dumps(valid_payload()), ProviderUsage(100, 20))]),
            sleeper=lambda _seconds: None,
        )
        estimate = generator.estimate(explanation_request())
        self.assertEqual(generator.model, "gpt-5.6-luna")
        self.assertGreater(estimate.per_attempt_microusd, 0)
        self.assertEqual(estimate.all_attempts_microusd, estimate.per_attempt_microusd * 2)
        self.assertEqual(
            observed_avalai_usage_cost_microusd(input_tokens=1_000_000, output_tokens=1_000_000),
            35_000_000,
        )
        self.assertEqual(
            estimate_cost_toman(1_000_000, toman_per_usd=Decimal("100000"), margin_ratio=Decimal("0.15")),
            Decimal("115000"),
        )
        self.assertEqual(
            conservative_microusd_cap(Decimal("100000"), toman_per_usd=Decimal("100000"),
                                      margin_ratio=Decimal("0.15")),
            869_565,
        )

    def test_invocation_records_avalai_not_direct_openai_and_no_payload(self):
        result = ProviderResult(
            json.dumps(valid_payload()), ProviderUsage(100, 20),
            request_id="req-avalai-2", provider_estimated_cost_toman=Decimal("9.75"),
        )
        generator = AvalAIExplanationGenerator(
            transport=FakeTransport([result]), guest_id=self.guest.id, operation_id=uuid.uuid4(),
            daily_budget_microusd=10_000_000, sleeper=lambda _seconds: None,
        )
        generator.generate(explanation_request(target_label="برچسب خصوصی"))

        invocation = AIInvocation.objects.get()
        self.assertEqual(invocation.provider, "avalai")
        self.assertEqual(invocation.model, "gpt-5.6-luna")
        self.assertEqual(invocation.provider_request_id, "req-avalai-2")
        self.assertEqual(invocation.provider_estimated_cost_toman, Decimal("9.75"))
        self.assertNotIn("برچسب خصوصی", repr(invocation.__dict__))

    @override_settings(
        BEFOREBUY_AI_MODE="live",
        BEFOREBUY_AI_PROVIDER="avalai",
        BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=False,
        AVALAI_API_KEY="",
        BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED=True,
        OPENAI_API_KEY="direct-openai-must-not-be-used",
    )
    def test_direct_openai_credentials_never_activate_iran_live_mode(self):
        selected = configured_explanation_generator(RequestFactory().get("/"), self.guest)
        self.assertIsInstance(selected, UnavailableLiveExplanationGenerator)
        self.assertIn("AvalAI eligibility", selected.reason)

    @override_settings(
        BEFOREBUY_AI_MODE="live",
        BEFOREBUY_AI_PROVIDER="avalai",
        BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=True,
        AVALAI_API_KEY="avalai-local-key",
        BEFOREBUY_AI_USD_TO_TOMAN_RATE="100000",
        BEFOREBUY_AI_DAILY_BUDGET_TOMAN="1000",
    )
    @patch("analysis.ai.factory.AvalAIExplanationGenerator.from_api_key")
    def test_factory_selects_only_approved_avalai_adapter(self, from_api_key):
        configured_explanation_generator(RequestFactory().get("/"), self.guest)
        from_api_key.assert_called_once()
        self.assertEqual(from_api_key.call_args.kwargs["model"], "gpt-5.6-luna")
