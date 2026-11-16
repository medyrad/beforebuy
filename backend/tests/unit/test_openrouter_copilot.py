import json
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import GuestContext, AIInvocation
from analysis.ai.openai_copilot import CopilotProviderError


@override_settings(COPILOT_OPENROUTER_SERVICE_ELIGIBLE=True, COPILOT_OPENROUTER_ROUTE_ELIGIBLE=True,
                   COPILOT_OPENROUTER_ELIGIBILITY_REFERENCE='synthetic-reviewed-evidence',
                   COPILOT_PHASE12_SPENDING_AUTHORIZED=False, COPILOT_OPERATION_CAP_MICROUSD=0,
                   COPILOT_SESSION_CAP_MICROUSD=0, COPILOT_DAILY_CAP_MICROUSD=0,
                   BEFOREBUY_RESEARCH_MODE='OFFLINE')
class OpenRouterTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))

    def adapter(self, events=None, current=lambda: True):
        from analysis.ai.openrouter_copilot import OpenRouterCopilotGenerator, MODEL
        from tests.unit.test_gapgpt_copilot import GapGPTCopilotTests
        payload = GapGPTCopilotTests.payload()
        stream = events if events is not None else [
            {'choices': [{'delta': {'content': payload}, 'finish_reason': None}], 'provider': 'Baidu', 'model': MODEL},
            {'choices': [{'delta': {}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 12, 'completion_tokens': 40, 'cost': 0}},
            {'done': True},
        ]
        return OpenRouterCopilotGenerator(guest_id=self.guest.id, operation_id=uuid.uuid4(),
            credential=lambda: 'synthetic-key', still_current=current,
            context={'current_message': 'گوشی من شکسته می‌خواهم آیفون ده بخرم.', 'brief': {},
                     'history': {'items': []}, 'choice': None, 'confirmed_memory': [], 'uploads': []},
            pricing=lambda: {'prompt': '0', 'completion': '0'}, transport=lambda **kw: iter(stream))

    def test_stream_validates_and_records_actual_usage_and_cost(self):
        adapter = self.adapter()
        chunks = list(adapter.generate())
        self.assertEqual(chunks[-1]['phase'], 'VALIDATED_BLOCK')
        self.assertIn('گوشی', adapter.final_text)
        row = AIInvocation.objects.get()
        self.assertEqual((row.provider, row.attempt_count, row.input_tokens), ('openrouter', 1, 12))
        self.assertEqual(row.provider_reported_cost_usd, 0)

    def test_ten_total_attempts_survive_new_owner_and_include_failures(self):
        from analysis.models import OpenRouterFreePilot
        for _ in range(10):
            with self.assertRaises(CopilotProviderError):
                list(self.adapter(events=[{'done': True}]).generate())
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        with self.assertRaisesRegex(CopilotProviderError, 'FREE_ATTEMPT_LIMIT'):
            list(self.adapter().generate())
        self.assertEqual(OpenRouterFreePilot.objects.get().attempts, 10)
        self.assertEqual(AIInvocation.objects.count(), 10)

    def test_unknown_nonzero_and_nonfinite_prices_rejected_before_generation(self):
        for prices in ({}, {'prompt': '0'}, {'prompt': '0', 'completion': '0.1'},
                       {'prompt': 'NaN', 'completion': '0'}, {'prompt': '0', 'completion': '0', 'request': '1'}):
            adapter = self.adapter()
            adapter.pricing = lambda: prices
            with self.assertRaisesRegex(CopilotProviderError, 'PRICE_UNVERIFIED'):
                list(adapter.generate())
        self.assertFalse(AIInvocation.objects.exists())

    def test_cancellation_stale_context_and_malformed_output_never_publish(self):
        for events in ([{'done': True}], [{'error': {'code': 429}}],
                       [{'choices': [{'delta': {'content': '{}'}, 'finish_reason': 'stop'}]}, {'done': True}]):
            adapter = self.adapter(events=events)
            with self.assertRaises(CopilotProviderError):
                list(adapter.generate())
            self.assertIsNone(adapter.final_text)
        adapter = self.adapter(current=lambda: False)
        with self.assertRaisesRegex(CopilotProviderError, 'STALE_OPERATION'):
            list(adapter.generate())
        self.assertEqual(AIInvocation.objects.count(), 3)

    def test_personal_context_and_paid_authorization_are_rejected(self):
        adapter = self.adapter()
        adapter.context['confirmed_memory'] = [{'private': 'must not transmit'}]
        with self.assertRaisesRegex(CopilotProviderError, 'SYNTHETIC_ONLY'):
            list(adapter.generate())
        with override_settings(COPILOT_PHASE12_SPENDING_AUTHORIZED=True):
            with self.assertRaisesRegex(CopilotProviderError, 'FREE_CONFIGURATION_REQUIRED'):
                list(self.adapter().generate())

    def test_missing_eligibility_never_calls_transport(self):
        with override_settings(COPILOT_OPENROUTER_SERVICE_ELIGIBLE=False):
            with self.assertRaisesRegex(CopilotProviderError, 'SERVICE_ELIGIBILITY_REQUIRED'):
                list(self.adapter().generate())

    def test_nonzero_returned_cost_freezes_future_attempts(self):
        from analysis.models import OpenRouterFreePilot
        adapter = self.adapter(events=[{'usage': {'cost': '0.0001'}}])
        with self.assertRaisesRegex(CopilotProviderError, 'NONZERO_RETURNED_COST'):
            list(adapter.generate())
        self.assertTrue(OpenRouterFreePilot.objects.get().blocked)
        with self.assertRaisesRegex(CopilotProviderError, 'FREE_ATTEMPT_LIMIT'):
            list(self.adapter().generate())
        self.assertEqual(AIInvocation.objects.count(), 1)

    def test_missing_returned_usage_cost_never_claims_validation(self):
        adapter = self.adapter()
        original = adapter.transport
        adapter.transport = lambda **kw: iter([{k: v for k, v in event.items() if k != 'usage'} for event in original(**kw)])
        with self.assertRaisesRegex(CopilotProviderError, 'COST_UNVERIFIED'):
            list(adapter.generate())
        self.assertIsNone(AIInvocation.objects.get().provider_reported_cost_usd)

    def test_cancellation_during_stream_closes_transport_without_final(self):
        state = {'current': True, 'closed': False}
        def events(**kw):
            try:
                state['current'] = False
                yield {'choices': []}
            finally:
                state['closed'] = True
        adapter = self.adapter(current=lambda: state['current'])
        adapter.transport = events
        with self.assertRaisesRegex(CopilotProviderError, 'STALE_OPERATION'):
            list(adapter.generate())
        self.assertTrue(state['closed'])
        self.assertIsNone(adapter.final_text)

    def test_http_transport_is_fixed_and_has_no_paid_fallback(self):
        import httpx2 as httpx
        from analysis.ai.openrouter_copilot import sdk_events, MODEL
        requests = []
        def handle(request):
            requests.append(request)
            body = json.loads(request.content)
            self.assertEqual(body['model'], MODEL)
            self.assertEqual(body['provider']['only'], ['baidu'])
            self.assertFalse(body['provider']['allow_fallbacks'])
            self.assertEqual(body['plugins'], [])
            self.assertNotIn('tools', body)
            return httpx.Response(200, text='data: [DONE]\n\n')
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            self.assertEqual(list(sdk_events(key='synthetic-key', messages=[], http_client=client)), [{'done': True}])
        self.assertEqual(str(requests[0].url), 'https://openrouter.ai/api/v1/chat/completions')

    def test_http_errors_and_malformed_stream_are_bounded_failures(self):
        import httpx2 as httpx
        from analysis.ai.openrouter_copilot import sdk_events
        for status, code in ((401, 'OPENROUTER_AUTH_FAILED'), (402, 'OPENROUTER_CREDIT_REQUIRED'),
                             (403, 'OPENROUTER_ACCESS_DENIED'), (429, 'OPENROUTER_RATE_LIMIT')):
            with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status))) as client:
                with self.assertRaisesRegex(CopilotProviderError, code):
                    list(sdk_events(key='synthetic', messages=[], http_client=client))
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text='data: not-json\n\n'))) as client:
            with self.assertRaisesRegex(CopilotProviderError, 'MALFORMED_OUTPUT'):
                list(sdk_events(key='synthetic', messages=[], http_client=client))

    def test_live_price_preflight_checks_exact_route_and_capabilities_without_credentials(self):
        import httpx2 as httpx
        from analysis.ai.openrouter_copilot import current_prices, MODEL, PRICING_ENDPOINT
        route = {'tag': 'baidu', 'status': 0, 'pricing': {'prompt': '0', 'completion': '0'},
                 'supported_parameters': ['response_format', 'structured_outputs']}
        cases = [route, {**route, 'tag': 'other'}, {**route, 'status': 1},
                 {**route, 'supported_parameters': []}, {**route, 'pricing': {'prompt': '1', 'completion': '0'}}]
        for index, endpoint in enumerate(cases):
            def handle(request):
                self.assertEqual(str(request.url), PRICING_ENDPOINT)
                self.assertNotIn('authorization', request.headers)
                return httpx.Response(200, json={'data': {'id': MODEL, 'endpoints': [endpoint]}})
            client = httpx.Client(transport=httpx.MockTransport(handle))
            with patch('analysis.ai.openrouter_copilot.httpx.Client', return_value=client):
                if index == 0:
                    self.assertEqual(current_prices(), {'prompt': '0', 'completion': '0'})
                else:
                    with self.assertRaisesRegex(CopilotProviderError, 'PRICE_UNVERIFIED'):
                        current_prices()
