"""One fixed, free-only, synthetic OpenRouter route; no implicit activation/retry."""
import json
import time
from decimal import Decimal, InvalidOperation

import httpx2 as httpx
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from analysis.models import AIInvocation, OpenRouterFreePilot, GuestContext
from .copilot_answer import AnswerPlanError, safe_lead, validate_conversational_plan
from .gapgpt_copilot import INSTRUCTIONS
from .gapgpt_copilot_contract import CONTRACT
from .openai_copilot import CopilotProviderError
from .provider_catalog import OPENROUTER_MODEL as MODEL

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
PRICING_ENDPOINT = f'https://openrouter.ai/api/v1/models/{MODEL}/endpoints'


def ensure_eligible():
    if not settings.COPILOT_OPENROUTER_SERVICE_ELIGIBLE:
        raise CopilotProviderError('SERVICE_ELIGIBILITY_REQUIRED')
    if not settings.COPILOT_OPENROUTER_ROUTE_ELIGIBLE or not settings.COPILOT_OPENROUTER_ELIGIBILITY_REFERENCE.strip():
        raise CopilotProviderError('ROUTE_ELIGIBILITY_REQUIRED')
    if (settings.COPILOT_PHASE12_SPENDING_AUTHORIZED or settings.COPILOT_PHASE12_TOTAL_CAP_TOMAN
            or any((settings.COPILOT_OPERATION_CAP_MICROUSD, settings.COPILOT_SESSION_CAP_MICROUSD,
                    settings.COPILOT_DAILY_CAP_MICROUSD)) or settings.BEFOREBUY_RESEARCH_MODE != 'OFFLINE'):
        raise CopilotProviderError('FREE_CONFIGURATION_REQUIRED')


def check_prices(prices):
    try:
        if not isinstance(prices, dict) or not {'prompt', 'completion'} <= prices.keys():
            raise ValueError
        for key, value in prices.items():
            if key == 'discount':
                continue
            if key not in {'prompt', 'completion', 'request', 'image', 'web_search', 'internal_reasoning',
                           'input_cache_read', 'input_cache_write'} or isinstance(value, bool):
                raise ValueError
            amount = Decimal(str(value))
            if not amount.is_finite() or amount != 0:
                raise ValueError
    except (ValueError, InvalidOperation):
        raise CopilotProviderError('PRICE_UNVERIFIED') from None


def current_prices():
    started = time.monotonic()
    try:
        with httpx.Client(timeout=8, trust_env=False, follow_redirects=False) as client:
            with client.stream('GET', PRICING_ENDPOINT) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 65536 or time.monotonic() - started > 12:
                        raise ValueError
        data = json.loads(body)['data']
        routes = [r for r in data['endpoints'] if r['tag'] == 'baidu']
        if data['id'] != MODEL or len(routes) != 1 or routes[0].get('status') != 0:
            raise ValueError
        route = routes[0]
        if not {'response_format', 'structured_outputs'} <= set(route.get('supported_parameters', [])):
            raise ValueError
        check_prices(route['pricing'])
        return route['pricing']
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise CopilotProviderError('PRICE_UNVERIFIED') from None


def error_code(status):
    return {401: 'OPENROUTER_AUTH_FAILED', 402: 'OPENROUTER_CREDIT_REQUIRED',
            403: 'OPENROUTER_ACCESS_DENIED', 429: 'OPENROUTER_RATE_LIMIT'}.get(status, 'OPENROUTER_UNAVAILABLE')


@sensitive_variables()
def sdk_events(*, key, messages, http_client=None):
    client = http_client or httpx.Client(timeout=8, trust_env=False, follow_redirects=False)
    started = time.monotonic()
    request = {'model': MODEL, 'messages': messages, 'stream': True, 'max_tokens': 1024,
               'stream_options': {'include_usage': True}, 'plugins': [],
               'provider': {'only': ['baidu'], 'allow_fallbacks': False, 'require_parameters': True,
                            'max_price': {'prompt': 0, 'completion': 0, 'request': 0}},
               'response_format': {'type': 'json_object'}}
    try:
        with client.stream('POST', ENDPOINT, headers={'Authorization': f'Bearer {key}'},
                           json=request, timeout=8, follow_redirects=False) as response:
            if response.status_code != 200:
                raise CopilotProviderError(error_code(response.status_code))
            pending = b''
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > 65536 or time.monotonic() - started > 20:
                    raise CopilotProviderError('OUTPUT_LIMIT')
                pending += chunk
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    if not line.startswith(b'data:'):
                        continue
                    value = line[5:].strip()
                    if value == b'[DONE]':
                        yield {'done': True}
                        return
                    event = json.loads(value)
                    if not isinstance(event, dict):
                        raise ValueError
                    yield event
    except CopilotProviderError:
        raise
    except (httpx.HTTPError, TimeoutError):
        raise CopilotProviderError('OPENROUTER_TIMEOUT') from None
    except (ValueError, UnicodeError):
        raise CopilotProviderError('MALFORMED_OUTPUT') from None
    finally:
        if http_client is None:
            client.close()


class OpenRouterCopilotGenerator:
    kind = 'OPENROUTER_FREE_CHAT'

    def __init__(self, *, guest_id, operation_id, credential, still_current, context,
                 pricing=current_prices, transport=sdk_events):
        self.guest_id, self.operation_id = guest_id, operation_id
        self.credential, self.still_current, self.context = credential, still_current, context
        self.pricing, self.transport = pricing, transport
        self.final_text = None

    @sensitive_variables()
    def generate(self):
        ensure_eligible()
        if not self.still_current():
            raise CopilotProviderError('STALE_OPERATION')
        if any(self.context.get(k) for k in ('confirmed_memory', 'choice', 'uploads')):
            raise CopilotProviderError('SYNTHETIC_ONLY')
        encoded = json.dumps(self.context, ensure_ascii=False)
        if len(encoded.encode()) > 16384:
            raise CopilotProviderError('INPUT_UNSUPPORTED')
        check_prices(self.pricing())
        key = self.credential()
        if not self.still_current():
            raise CopilotProviderError('STALE_OPERATION')
        with transaction.atomic():
            guest = GuestContext.objects.select_for_update().get(id=self.guest_id)
            if guest.access_expires_at <= timezone.now():
                raise CopilotProviderError('OWNER_EXPIRED')
            OpenRouterFreePilot.objects.get_or_create(id='initial')
            allowance = OpenRouterFreePilot.objects.select_for_update().get(id='initial')
            if allowance.blocked or allowance.attempts >= 10:
                raise CopilotProviderError('FREE_ATTEMPT_LIMIT')
            allowance.attempts += 1
            allowance.save(update_fields=['attempts'])
            row = AIInvocation.objects.create(guest_context=guest, operation_id=self.operation_id,
                provider='openrouter', model=MODEL, hosting_provider='baidu', prompt_version='COPILOT-FREE-v1',
                schema_version='COPILOT-CONVERSATION-v1', status='RESERVED', attempt_count=1)
        started = time.monotonic()
        stream = None
        success = False
        code = 'OPENROUTER_INTERRUPTED'
        try:
            yield {'text': safe_lead(self.context), 'phase': 'PROVISIONAL_CONTEXT'}
            messages = [{'role': 'system', 'content': INSTRUCTIONS + '\nCONTRACT\n' + json.dumps(CONTRACT)},
                        {'role': 'user', 'content': 'CONTEXT\n' + encoded}]
            stream = self.transport(key=key, messages=messages)
            buffer = ''
            stopped = done = route_seen = False
            for event in stream:
                if not self.still_current():
                    raise CopilotProviderError('STALE_OPERATION')
                if time.monotonic() - started > 20:
                    raise CopilotProviderError('DEADLINE_EXCEEDED')
                if event.get('error'):
                    raise CopilotProviderError(error_code(event['error'].get('code')))
                if event.get('provider'):
                    if event['provider'].lower() not in ('baidu', 'baidu qianfan'):
                        raise CopilotProviderError('ROUTE_MISMATCH')
                    route_seen = True
                if event.get('model') and event['model'] not in (MODEL, MODEL.removesuffix(':free')):
                    raise CopilotProviderError('MODEL_MISMATCH')
                usage = event.get('usage') or {}
                if all(type(usage.get(k)) is int and 0 <= usage[k] <= 1000000 for k in ('prompt_tokens', 'completion_tokens')):
                    row.input_tokens, row.output_tokens = usage['prompt_tokens'], usage['completion_tokens']
                    row.usage_complete = True
                if usage.get('cost') is not None:
                    amount = Decimal(str(usage['cost']))
                    if not amount.is_finite() or amount < 0 or amount > 100000:
                        raise CopilotProviderError('COST_UNVERIFIED')
                    row.provider_reported_cost_usd = amount
                    if amount != 0:
                        OpenRouterFreePilot.objects.filter(id='initial').update(blocked=True)
                        raise CopilotProviderError('NONZERO_RETURNED_COST')
                for choice in event.get('choices', []):
                    if choice.get('finish_reason'):
                        if choice['finish_reason'] != 'stop':
                            raise CopilotProviderError('INCOMPLETE_OUTPUT')
                        stopped = True
                    delta = choice.get('delta', {}).get('content') or ''
                    if not isinstance(delta, str):
                        raise CopilotProviderError('MALFORMED_OUTPUT')
                    buffer += delta
                    if len(buffer.encode()) > 16384:
                        raise CopilotProviderError('OUTPUT_LIMIT')
                done = done or event.get('done') is True
            if not (done and stopped and route_seen):
                raise CopilotProviderError('INCOMPLETE_OUTPUT')
            if not row.usage_complete or row.provider_reported_cost_usd is None:
                raise CopilotProviderError('COST_UNVERIFIED')
            rendered = validate_conversational_plan(json.loads(buffer), self.context)
            if not self.still_current():
                raise CopilotProviderError('STALE_OPERATION')
            self.final_text = rendered.final_text
            for chunk in rendered.chunks:
                if not self.still_current():
                    self.final_text = None
                    raise CopilotProviderError('STALE_OPERATION')
                yield {'text': chunk, 'phase': 'VALIDATED_BLOCK'}
            success = True
        except CopilotProviderError as exc:
            code = str(exc)
            raise
        except (ValueError, TypeError, KeyError, AttributeError, InvalidOperation, AnswerPlanError):
            code = 'MALFORMED_OUTPUT'
            raise CopilotProviderError(code) from None
        finally:
            if stream is not None and hasattr(stream, 'close'):
                stream.close()
            row.status = 'SUCCEEDED' if success else 'FAILED'
            row.error_class = None if success else code
            row.completed_at = timezone.now()
            row.latency_ms = int((time.monotonic() - started) * 1000)
            row.save()
