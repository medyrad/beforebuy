import json
import uuid
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import AIInvocation, GuestContext


class GapGPTCopilotTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        self.context = {
            "current_message": "گوشی من شکسته می‌خواهم آیفون ده بخرم.",
            "brief": {}, "history": {"items": [], "omitted_count": 0}, "choice": None,
            "confirmed_memory": [], "uploads": [],
        }

    @staticmethod
    def payload():
        return json.dumps({
            "conversation": {
                "acknowledgement": "متوجه شدم گوشی فعلی شما شکسته و به خرید آیفون ده فکر می‌کنید.",
                "next_question": "سقف بودجه‌تان برای این خرید چقدر است؟",
                "brief_proposal": {"category": "گوشی موبایل", "selected_product_label": "آیفون ده"},
            },
            "answer_plan": {
                "answer_type": "CLARIFICATION", "lead_key": "NEEDS_CONTEXT",
                "clarification_key": "none", "blocks": [],
            },
        }, ensure_ascii=False)

    def adapter(self, events):
        from analysis.ai.gapgpt_copilot import GapGPTCopilotGenerator
        return GapGPTCopilotGenerator(
            guest_id=self.guest.id, operation_id=uuid.uuid4(),
            model="gapgpt-deepseek-v4.1-flash", transport=lambda **request: iter(events),
            credential=lambda: "synthetic-only", still_current=lambda: True,
            operation_cap=10000, session_cap=20000, daily_cap=100000,
            context=self.context,
        )

    def test_streamed_json_becomes_natural_question_and_accounts_usage(self):
        events = [
            {"type": "response.output_text.delta", "delta": self.payload()},
            {"type": "response.completed", "response": {"status": "completed", "usage": {
                "input_tokens": 80, "output_tokens": 30,
            }}},
        ]
        adapter = self.adapter(events)
        chunks = list(adapter.generate())
        self.assertEqual(chunks[0]["phase"], "PROVISIONAL_CONTEXT")
        self.assertIn("گوشی فعلی شما شکسته", adapter.final_text)
        self.assertIn("سقف بودجه‌تان", adapter.final_text)
        self.assertIn("پیشنهاد برای تأیید", adapter.final_text)
        self.assertIn("آیفون ده", adapter.final_text)
        row = AIInvocation.objects.get()
        self.assertEqual(row.provider, "gapgpt-copilot")
        self.assertEqual((row.input_tokens, row.output_tokens), (80, 30))

    def test_unsupported_price_in_free_text_is_rejected(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        data = json.loads(self.payload())
        data["conversation"]["acknowledgement"] = "قیمت امروز این گوشی ۲۰ میلیون تومان است."
        events = [
            {"type": "response.output_text.delta", "delta": json.dumps(data, ensure_ascii=False)},
            {"type": "response.completed", "response": {"status": "completed"}},
        ]
        with self.assertRaisesRegex(CopilotProviderError, "MALFORMED_OUTPUT"):
            list(self.adapter(events).generate())

    def test_invalid_brief_proposal_is_rejected_instead_of_applied(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        data = json.loads(self.payload())
        data["conversation"]["brief_proposal"] = {"authoritative_price": 20}
        events = [
            {"type": "response.output_text.delta", "delta": json.dumps(data, ensure_ascii=False)},
            {"type": "response.completed", "response": {"status": "completed"}},
        ]
        with self.assertRaisesRegex(CopilotProviderError, "MALFORMED_OUTPUT"):
            list(self.adapter(events).generate())

    @override_settings(COPILOT_PHASE12_SPENDING_AUTHORIZED=True,
                       COPILOT_PHASE12_TOTAL_CAP_TOMAN=Decimal('0.01'),
                       COPILOT_USD_TO_TOMAN_RATE=100000, COPILOT_EXCHANGE_MARGIN_RATIO=Decimal('0.15'))
    def test_hard_total_toman_authorization_rejects_before_transport(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        called = False

        def transport(**request):
            nonlocal called
            called = True
            return iter(())

        adapter = self.adapter([])
        adapter.transport = transport
        with self.assertRaisesRegex(CopilotProviderError, 'BUDGET_REJECTED'):
            list(adapter.generate())
        self.assertFalse(called)

    def test_transient_empty_first_attempt_retries_once_and_accounts_missing_usage(self):
        from analysis.ai.openai_adapter import ProviderTransientError
        calls = 0

        def transport(**request):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ProviderTransientError('PROVIDER_TIMEOUT')
            return iter([
                {"type": "response.output_text.delta", "delta": self.payload()},
                {"type": "response.completed", "response": {"status": "completed"}},
            ])

        adapter = self.adapter([])
        adapter.transport = transport
        list(adapter.generate())
        row = AIInvocation.objects.get()
        self.assertEqual((calls, row.attempt_count), (2, 2))
        self.assertFalse(row.usage_complete)
        self.assertGreater(row.unknown_cost_microusd, 0)

    def test_stale_operation_stops_before_transport_and_accounting_reservation(self):
        adapter = self.adapter([])
        adapter.still_current = lambda: False
        with self.assertRaisesRegex(Exception, 'STALE_OPERATION'):
            list(adapter.generate())
        self.assertFalse(AIInvocation.objects.exists())

    def test_sdk_uses_fixed_chat_completions_endpoint_without_schema_claim(self):
        import httpx2 as httpx
        from analysis.ai.gapgpt_copilot import sdk_chat_events

        def handler(request):
            self.assertEqual(str(request.url), "https://api.gapgpt.app/v1/chat/completions")
            body = json.loads(request.content)
            self.assertEqual(body["model"], "gapgpt-deepseek-v4.1-flash")
            self.assertTrue(body["stream"])
            self.assertNotIn("response_format", body)
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=(
                'data: {"id":"chatcmpl_synthetic","object":"chat.completion.chunk","created":1,'
                '"model":"gapgpt-deepseek-v4.1-flash","choices":[{"index":0,"delta":{"content":"{}"},'
                '"finish_reason":null}]}\n\n'
                'data: [DONE]\n\n'
            ))

        events = list(sdk_chat_events(
            key="synthetic-not-real", model="gapgpt-deepseek-v4.1-flash",
            messages=[{"role": "user", "content": "test"}], max_tokens=256, stream=True,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        ))
        self.assertEqual(events[0]["delta"], "{}")
