"""Bounded, ephemeral context for contextual copilot answers.

Provider input may contain user prose.  The persisted manifest deliberately
contains only identifiers, revisions, hashes and expiry anchors.
"""
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from analysis.models import ChoiceSet, CopilotSettings, Message, PreferenceMemory, SourceSnapshot, StreamOperation


@dataclass(frozen=True)
class CopilotContextBundle:
    provider_input: dict
    manifest: dict
    fingerprint: str
    limited_reason: str | None = None


def assemble_context(operation_id):
    operation = (StreamOperation.objects.select_related('conversation__brief', 'user_message')
                 .get(id=operation_id))
    conversation = operation.conversation
    brief = conversation.brief
    preferences, _ = CopilotSettings.objects.get_or_create(guest_context_id=conversation.guest_context_id)
    latest = (Message.objects.filter(conversation=conversation, role='USER', state='ACCEPTED')
              .order_by('-created_at', '-id').first())
    brief_data = {
        'revision': brief.revision,
        'recipient_context': brief.recipient_context,
        'category': brief.category,
        'selected_product_label': brief.selected_product_label,
        'budget_toman': brief.budget_toman,
        'use_cases': deepcopy(brief.use_cases),
        'hard_constraints': deepcopy(brief.hard_constraints),
        'unknowns': deepcopy(brief.unknowns),
        'contradictions': deepcopy(brief.contradictions),
        'comparison': deepcopy(brief.comparison),
        'confirmed': brief.confirmed,
    }
    core = {'current_message': operation.user_message.text if operation.user_message else '', 'brief': brief_data}
    if len(_encoded(core)) > getattr(settings, 'COPILOT_CONTEXT_CRITICAL_BYTES', 32768):
        manifest = _manifest(operation, preferences, latest, brief, None, [], [])
        return CopilotContextBundle({}, manifest, _fingerprint({}), 'CRITICAL_CONTEXT_LIMIT')

    choice = _current_choice(conversation)
    memory = _current_memory(conversation, preferences, brief)
    history = _bounded_history(operation)
    uploads = list(operation.user_message.uploads.filter(expires_at__gt=timezone.now()).order_by('id')) \
        if operation.user_message_id else []
    provider_input = {
        **core,
        'history': history,
        'choice': _safe_choice(choice.result) if choice else None,
        'confirmed_memory': [
            {'criterion': deepcopy(item.criterion), 'category': item.category} for item in memory
        ],
        'uploads': [{'id': str(item.id), 'media_type': item.media_type, 'sha256': item.sha256} for item in uploads],
    }
    total_limit = getattr(settings, 'COPILOT_CONTEXT_TOTAL_BYTES', 49152)
    if len(_encoded(provider_input)) > total_limit:
        provider_input['history'] = {'items': [], 'omitted_count': history['omitted_count'] + len(history['items']),
                                     'truncated': True}
    if len(_encoded(provider_input)) > total_limit:
        manifest = _manifest(operation, preferences, latest, brief, choice, memory, uploads)
        return CopilotContextBundle({}, manifest, _fingerprint({}), 'TOTAL_CONTEXT_LIMIT')
    manifest = _manifest(operation, preferences, latest, brief, choice, memory, uploads)
    return CopilotContextBundle(provider_input, manifest, _fingerprint(provider_input), None)


def manifest_is_current(operation_id, manifest, fingerprint):
    try:
        current = assemble_context(operation_id)
    except StreamOperation.DoesNotExist:
        return False
    return (current.limited_reason is None and current.manifest == manifest
            and current.fingerprint == fingerprint)


def pin_context(operation_id, lease_owner):
    """Persist only non-secret anchors after checking current lease ownership."""
    bundle = assemble_context(operation_id)
    if bundle.limited_reason:
        return bundle
    updated = StreamOperation.objects.filter(
        id=operation_id, status='RUNNING', lease_owner=lease_owner,
        lease_expires_at__gt=timezone.now(), cancel_requested_at__isnull=True,
    ).update(context_manifest=bundle.manifest, context_fingerprint=bundle.fingerprint)
    if updated != 1:
        return CopilotContextBundle({}, bundle.manifest, bundle.fingerprint, 'STALE_OPERATION')
    return bundle


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _fingerprint(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _bounded_history(operation):
    eligible = Message.objects.filter(
        conversation_id=operation.conversation_id,
        created_at__lte=operation.user_message.created_at,
    ).filter(Q(role='USER', state='ACCEPTED') | Q(role='ASSISTANT', state='FINAL')) \
        .exclude(id=operation.user_message_id)
    rows = list(eligible.order_by('-created_at', '-id')[:16])
    budget = getattr(settings, 'COPILOT_CONTEXT_HISTORY_BYTES', 6000)
    kept = []
    used = 0
    for row in rows:
        item = {'role': row.role, 'text': row.text}
        size = len(_encoded(item))
        if used + size > budget:
            break
        kept.append(item)
        used += size
    kept.reverse()
    omitted = max(0, eligible.count() - len(kept))
    return {'items': kept, 'omitted_count': omitted, 'truncated': omitted > 0}


def _current_choice(conversation):
    now = timezone.now()
    choice = (ChoiceSet.objects.filter(
        conversation=conversation,
        brief_revision=conversation.brief_revision,
        generation_epoch=conversation.generation_epoch,
        evidence_valid_until__gt=now,
    ).order_by('-created_at', '-id').first())
    if choice is None:
        return None
    snapshot_ids = {str(value) for value in choice.snapshot_ids}
    if snapshot_ids:
        found = {str(value) for value in SourceSnapshot.objects.filter(
            id__in=snapshot_ids, research_job__conversation=conversation,
            raw_expires_at__gt=now,
        ).values_list('id', flat=True)}
        if found != snapshot_ids:
            return None
    return choice


def _current_memory(conversation, preferences, brief):
    if conversation.temporary or not preferences.memory_enabled or not brief.category:
        return []
    scope = {'GIFT': 'RECIPIENT', 'HOUSEHOLD': 'HOUSEHOLD'}.get(brief.recipient_context, 'SELF')
    explicit = {item.get('field') for item in (brief.comparison or {}).get('criteria', [])
                if item.get('scope') == scope}
    now = timezone.now()
    values = PreferenceMemory.objects.filter(
        guest_context_id=conversation.guest_context_id,
        category=brief.category,
        state='CONFIRMED',
        confirmed_at__isnull=False,
        expires_at__gt=now,
    ).order_by('created_at', 'id')
    return [item for item in values
            if item.criterion.get('scope') == scope and item.criterion.get('field') not in explicit]


def _safe_choice(result):
    safe = {key: deepcopy(result.get(key)) for key in
            ('rule_version', 'outcome', 'leaders', 'clarification', 'intent', 'scope', 'no_alternatives')}
    safe['items'] = []
    for item in result.get('items', [])[:4]:
        clean = {key: deepcopy(item.get(key)) for key in (
            'id', 'name', 'intended', 'group', 'total', 'item_price', 'cost_state',
            'checks', 'unknowns', 'tradeoffs', 'coverage', 'would_change_if',
        )}
        clean['sources'] = [{key: deepcopy(source.get(key)) for key in
                             ('id', 'attribution', 'observed_at', 'fresh_until', 'fresh')}
                            for source in item.get('sources', [])]
        clean['offers'] = [{key: deepcopy(offer.get(key)) for key in (
            'id', 'seller', 'price', 'shipping', 'mandatory', 'stock', 'fresh',
            'source_id', 'attribution', 'observation_kind', 'observed_at',
        )} for offer in item.get('offers', [])[:8]]
        safe['items'].append(clean)
    return safe


def _manifest(operation, preferences, latest, brief, choice, memory, uploads):
    return {
        'conversation_id': str(operation.conversation_id),
        'operation_id': str(operation.id),
        'latest_user_message_id': str(latest.id) if latest else None,
        'brief': {'revision': brief.revision, 'generation_epoch': operation.conversation.generation_epoch},
        'settings': {'revision': preferences.revision, 'model': preferences.model},
        'choice': None if choice is None else {
            'id': str(choice.id), 'brief_revision': choice.brief_revision,
            'generation_epoch': choice.generation_epoch,
            'snapshot_ids': sorted(str(value) for value in choice.snapshot_ids),
            'evidence_valid_until': choice.evidence_valid_until.isoformat(),
        },
        'memory': [{'id': str(item.id), 'revision': item.revision,
                    'expires_at': item.expires_at.isoformat()} for item in memory],
        'uploads': [{'id': str(item.id), 'sha256': item.sha256,
                     'expires_at': item.expires_at.isoformat()} for item in uploads],
    }
