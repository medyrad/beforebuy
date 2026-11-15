import json
import uuid
from types import SimpleNamespace
from unittest.mock import Mock
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from analysis.models import GuestContext, AIInvocation


class CopilotAdapterTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now()+timedelta(days=1))

    def adapter(self, events, **kwargs):
        from analysis.ai.openai_copilot import OpenAICopilotGenerator
        return OpenAICopilotGenerator(guest_id=self.guest.id, operation_id=uuid.uuid4(), model='gpt-6-luna',
            transport=lambda **request: iter(events), credential=lambda: 'synthetic-only',
            still_current=lambda: True, operation_cap=10000, session_cap=20000, daily_cap=100000,
            input_text='فقط نیاز را روشن کن', **kwargs)

    def test_events_to_provisional_and_validated_final_usage(self):
        events = [{'type': 'response.output_text.delta', 'delta': '{"question_key":"budget_toman"}'},
                  {'type': 'response.completed', 'response': {'id': 'resp_synthetic', 'status': 'completed',
                   'usage': {'input_tokens': 40, 'output_tokens': 10}}}]
        adapter = self.adapter(events)
        self.assertTrue(list(adapter.generate()))
        self.assertEqual(adapter.final_text, 'سقف بودجهٔ این خرید چقدر است؟')
        row = AIInvocation.objects.get()
        self.assertEqual((row.input_tokens, row.output_tokens, row.attempt_count), (40, 10, 1))
        self.assertTrue(row.usage_complete)

    def test_malformed_refusal_and_missing_completion_do_not_finalize(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        for events in [[{'type': 'response.output_text.delta', 'delta': '{"rank":1}'}],
                       [{'type': 'response.refusal.delta', 'delta': 'no'}],
                       [{'type': 'response.completed', 'response': {'status': 'completed'}}]]:
            with self.assertRaises(CopilotProviderError): list(self.adapter(events).generate())
        self.assertFalse(AIInvocation.objects.filter(status='succeeded').exists())

    def test_cancel_cost_caps_and_transient_retry(self):
        from analysis.ai.openai_copilot import CopilotProviderError, OpenAICopilotGenerator
        from analysis.ai.openai_adapter import ProviderTransientError
        transport = Mock(side_effect=ProviderTransientError('safe'))
        adapter = OpenAICopilotGenerator(guest_id=self.guest.id, operation_id=uuid.uuid4(), model='gpt-6-luna',
            transport=transport, credential=lambda: 'synthetic', still_current=lambda: True,
            operation_cap=10000, session_cap=20000, daily_cap=100000, input_text='test')
        with self.assertRaises(CopilotProviderError): list(adapter.generate())
        self.assertEqual(transport.call_count, 2)
        self.assertEqual(AIInvocation.objects.get().attempt_count, 2)
        self.assertGreater(AIInvocation.objects.get().unknown_cost_microusd, 0)
        adapter.operation_id = uuid.uuid4(); adapter.still_current = lambda: False
        with self.assertRaises(CopilotProviderError): list(adapter.generate())
        self.assertEqual(transport.call_count, 2)
        adapter.still_current = lambda: True; adapter.operation_cap = 1
        with self.assertRaises(CopilotProviderError): list(adapter.generate())
        self.assertEqual(transport.call_count, 2)

    def test_discovery_intersection_and_saved_unavailable(self):
        from analysis.ai.copilot_catalog import discover_models
        result = discover_models(['gpt-6-luna', 'unknown-model'], saved_model='missing')
        self.assertEqual([m['id'] for m in result['items']], ['gpt-6-luna'])
        self.assertEqual(result['saved_status'], 'UNAVAILABLE')
        self.assertEqual(discover_models(None, saved_model='gpt-6-luna')['saved_status'], 'ACCOUNT_UNVERIFIED')

    def test_sdk_transport_uses_actual_sse_protocol_and_safe_http_error(self):
        import httpx2 as httpx
        from analysis.ai.openai_copilot import sdk_events, CopilotProviderError
        from unittest.mock import patch
        original = httpx.Client
        def handler(request):
            data = json.loads(request.content)
            self.assertFalse(data['store'])
            self.assertTrue(data['stream'])
            self.assertEqual(str(request.url), 'https://api.openai.com/v1/responses')
            return httpx.Response(200, headers={'content-type': 'text/event-stream', 'x-request-id': 'req_synthetic'},
                text='data: {"type":"response.output_text.delta","delta":"abc","sequence_number":1,"item_id":"msg_1","output_index":0,"content_index":0,"logprobs":[]}\n\ndata: [DONE]\n\n')
        events = list(sdk_events(key='synthetic-not-real', model='gpt-6-luna', input='test', stream=True, store=False,
                                http_client=original(transport=httpx.MockTransport(handler))))
        self.assertEqual(events[0]['request_id'], 'req_synthetic')
        self.assertEqual(events[1]['delta'], 'abc')
        def denied(request):
            return httpx.Response(401, json={'error': {'message': 'synthetic-sensitive-do-not-echo', 'type': 'invalid_request_error'}})
        with self.assertRaises(CopilotProviderError) as error:
            list(sdk_events(key='synthetic-not-real', model='gpt-6-luna', input='test', stream=True, store=False,
                            http_client=original(transport=httpx.MockTransport(denied))))
        self.assertNotIn('sensitive', str(error.exception))
        from analysis.ai.openai_adapter import ProviderTransientError
        def timeout(request):
            raise httpx.ReadTimeout('synthetic-sensitive-timeout', request=request)
        with self.assertRaisesRegex(ProviderTransientError, '^PROVIDER_TIMEOUT$'):
            list(sdk_events(key='synthetic-not-real', model='gpt-6-luna', input='test', stream=True, store=False,
                            http_client=original(transport=httpx.MockTransport(timeout))))

    def test_session_limit_unknown_usage_and_image_request(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        requests = []
        def transport(**request):
            requests.append(request)
            return iter([{'type': 'response.output_text.delta', 'delta': '{"question_key":"none"}'},
                         {'type': 'response.completed', 'response': {'status': 'completed'}}])
        adapter = self.adapter([], images=['data:image/png;base64,c3ludGhldGlj'])
        adapter.transport = transport
        list(adapter.generate())
        self.assertEqual(requests[0]['input'][0]['content'][1]['type'], 'input_image')
        row = AIInvocation.objects.get()
        self.assertFalse(row.usage_complete)
        self.assertGreater(row.unknown_cost_microusd, 0)
        adapter.operation_id = uuid.uuid4(); adapter.session_cap = row.estimated_cost_microusd
        with self.assertRaisesRegex(CopilotProviderError, 'SESSION_COST_LIMIT'): list(adapter.generate())
        self.assertEqual(len(requests), 1)

    def test_cancellation_during_stream_closes_and_never_finalizes(self):
        from analysis.ai.openai_copilot import CopilotProviderError
        current = [True]; closed = []
        def stream(**request):
            try:
                yield {'type': 'response.output_text.delta', 'delta': '{'}
                current[0] = False
                yield {'type': 'response.output_text.delta', 'delta': '}'}
            finally: closed.append(True)
        adapter = self.adapter([]); adapter.transport = stream; adapter.still_current = lambda: current[0]
        with self.assertRaisesRegex(CopilotProviderError, 'STALE_OPERATION'): list(adapter.generate())
        self.assertEqual(closed, [True])
        self.assertIsNone(adapter.final_text)

    def test_session_cost_limit_survives_invocation_metadata_cleanup(self):
        from django.core.management import call_command
        from analysis.ai.openai_copilot import CopilotProviderError
        from io import StringIO
        events = [{'type': 'response.output_text.delta', 'delta': '{"question_key":"none"}'},
                  {'type': 'response.completed', 'response': {'status': 'completed'}}]
        adapter = self.adapter(events)
        list(adapter.generate())
        row = AIInvocation.objects.get()
        # One missing-usage attempt consumes half the two-attempt reservation.
        # This cap permits a fresh reservation only if prior spending was forgotten.
        adapter.session_cap = row.reserved_cost_microusd
        AIInvocation.objects.filter(pk=row.pk).update(created_at=timezone.now()-timedelta(days=91))
        call_command('purge_expired_analyses', stdout=StringIO())
        self.assertFalse(AIInvocation.objects.exists())
        adapter.operation_id = uuid.uuid4()
        with self.assertRaisesRegex(CopilotProviderError, 'SESSION_COST_LIMIT'):
            list(adapter.generate())

    @override_settings(COPILOT_AI_MODE='live', COPILOT_REGION_REVIEWED=True)
    def test_iran_cannot_be_bypassed_by_flag_or_key(self):
        from analysis.ai.openai_copilot import ensure_live_eligible, CopilotProviderError
        with self.assertRaisesRegex(CopilotProviderError, 'REGION_BLOCKED'):
            ensure_live_eligible()
