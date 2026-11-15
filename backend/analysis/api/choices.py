"""Owner-scoped, deterministic comparison; no retrieval or model calls."""
from uuid import UUID

from django.db import transaction
from django.http import JsonResponse
from rest_framework.response import Response

from analysis.guest import get_or_create_guest
from analysis.ranking.demo import DEMO, seed_demo
from analysis.ranking.engine import CRITERIA, compare
from analysis.ranking.service import candidates_for, publish_choice, serialize_choice
from .base import CsrfProtectedAPIView
from .conversations import active_conversation, error


def revision_error(data, conversation):
    revision = data.get('expected_revision')
    if type(revision) is not int or revision < 0:
        return error('VALIDATION_ERROR', 'نسخهٔ نیاز خرید نامعتبر است.', 422)
    if revision != conversation.brief_revision or not conversation.brief.confirmed:
        return error('STALE_BRIEF_REVISION', 'نیاز خرید را دوباره تأیید کنید.', 409)
    return None


class ChoiceCandidatesView(CsrfProtectedAPIView):
    def get(self, request, conversation_id):
        c = active_conversation(get_or_create_guest(request), conversation_id)
        return Response({'items': candidates_for(c)})


class ChoiceDemoView(CsrfProtectedAPIView):
    @transaction.atomic
    def post(self, request, conversation_id):
        c = active_conversation(get_or_create_guest(request), conversation_id, lock=True)
        failure = revision_error(request.data, c)
        if failure is not None: return failure
        category = request.data.get('category')
        if not isinstance(category, str) or category not in DEMO:
            return error('VALIDATION_ERROR', 'دستهٔ نمونه نامعتبر است.', 422)
        # Reuse the owner's existing examples instead of multiplying products on retry.
        existing = [v['id'] for v in sorted(candidates_for(c), key=lambda v: v['name']) if v['category'] == category and
                    any(s['label'].startswith('نمونهٔ مصنوعی آموزشی') and s['fresh'] for s in v['sources'])]
        return Response({'variant_ids': existing[:3] or seed_demo(c, category), 'attribution': 'SYNTHETIC'}, status=201)


class ChoiceDeskView(CsrfProtectedAPIView):
    def get(self, request, conversation_id):
        c = active_conversation(get_or_create_guest(request), conversation_id)
        choice = c.choice_sets.order_by('-created_at', '-id').first()
        return Response(serialize_choice(choice, c)) if choice else JsonResponse(None, safe=False)

    def post(self, request, conversation_id):
        guest = get_or_create_guest(request)
        c = active_conversation(guest, conversation_id)
        failure = revision_error(request.data, c)
        if failure is not None: return failure
        ids = request.data.get('variant_ids')
        intended = request.data.get('intended_variant_id')
        if not isinstance(ids, list) or not 1 <= len(ids) <= 4 or any(not isinstance(i, str) for i in ids):
            return error('VALIDATION_ERROR', 'یک محصول و حداکثر سه جایگزین را انتخاب کنید.', 422)
        try:
            ids = [str(UUID(i)) for i in ids]
            intended = str(UUID(intended))
        except (ValueError, TypeError, AttributeError):
            return error('VALIDATION_ERROR', 'شناسهٔ محصول نامعتبر است.', 422)
        if len(set(ids)) != len(ids) or intended not in ids:
            return error('VALIDATION_ERROR', 'محصول موردنظر باید در انتخاب‌های یکتا باشد.', 422)
        candidates = candidates_for(c, ids)
        if len(candidates) != len(ids) or len({v['product_id'] for v in candidates}) != len(ids):
            return error('EVIDENCE_UNAVAILABLE', 'شواهد محصولات انتخابی در این گفت‌وگو موجود نیست.', 422)
        categories = {v['category'] for v in candidates}
        if len(categories) != 1:
            return error('VALIDATION_ERROR', 'محصولات باید از یک دسته باشند.', 422)
        category = next(iter(categories))
        if c.brief.category in CRITERIA and category != c.brief.category:
            return error('VALIDATION_ERROR', 'دستهٔ محصول با نیاز تأییدشده یکسان نیست.', 422)
        criteria = c.brief.comparison.get('criteria', [])
        if any(criterion['field'] not in CRITERIA.get(category, {}) for criterion in criteria):
            return error('VALIDATION_ERROR', 'معیار انتخابی با دستهٔ محصول سازگار نیست.', 422)
        brief = {key: getattr(c.brief, key) for key in ('comparison', 'recipient_context', 'budget_toman', 'hard_constraints', 'contradictions')}
        result = compare(brief, candidates, intended)
        snapshots = sorted({s['id'] for v in candidates for s in v['sources']})
        try:
            choice = publish_choice(c.id, guest.id, c.brief_revision, c.generation_epoch, result, snapshots)
        except ValueError:
            return error('STALE_COMPARISON', 'نیاز یا شواهد تغییر کرده؛ مقایسه را دوباره بسازید.', 409)
        return Response(serialize_choice(choice, c), status=201)
