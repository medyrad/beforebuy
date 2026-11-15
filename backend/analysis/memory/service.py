"""Explicit structured preference candidates, never broad natural-language inference."""
from copy import deepcopy
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from analysis.models import CopilotSettings, PreferenceMemory
from analysis.ranking.engine import CRITERIA


def preferences(guest):
    now = timezone.now()
    return PreferenceMemory.objects.filter(guest_context=guest, expires_at__gt=now,
        source_conversation__expires_at__gt=now, guest_context__access_expires_at__gt=now).order_by('created_at', 'id')


def consent(guest):
    return CopilotSettings.objects.filter(guest_context=guest, memory_enabled=True).exists()


def scope_for(brief):
    return {'SELF': 'SELF', 'GIFT': 'RECIPIENT', 'HOUSEHOLD': 'HOUSEHOLD'}.get(brief.recipient_context)


def validate_criterion(category, criterion):
    if not isinstance(criterion, dict) or set(criterion) != {'field', 'expected', 'kind', 'scope'}:
        raise ValidationError('ترجیح ساختاریافته نامعتبر است.')
    field = criterion['field']
    if not isinstance(field, str) or field not in CRITERIA.get(category, {}):
        raise ValidationError('ویژگی این دسته پشتیبانی نمی‌شود.')
    value = criterion['expected']
    if type(value) is not CRITERIA[category][field] or (type(value) is int and not 1 <= value <= 100000):
        raise ValidationError('مقدار ترجیح نامعتبر است.')
    if criterion['kind'] not in ('HARD', 'PREFERENCE') or criterion['scope'] not in ('SELF', 'RECIPIENT', 'HOUSEHOLD'):
        raise ValidationError('نوع یا مخاطب ترجیح نامعتبر است.')
    return deepcopy(criterion)


def serialize(item):
    return {'id': str(item.id), 'category': item.category, 'criterion': item.criterion, 'state': item.state,
            'revision': item.revision, 'source_conversation_id': str(item.source_conversation_id),
            'source_revision': item.source_revision, 'provenance': 'EXPLICIT_STRUCTURED_CANDIDATE',
            'expires_at': item.expires_at.isoformat()}


def propose(guest, conversation):
    brief = conversation.brief
    items = []
    for criterion in brief.comparison.get('criteria', []):
        if criterion['scope'] != scope_for(brief):
            continue
        criterion = validate_criterion(brief.category, criterion)
        item, _ = PreferenceMemory.objects.get_or_create(guest_context=guest, source_conversation=conversation,
            source_revision=brief.revision, category=brief.category, criterion=criterion,
            defaults={'expires_at': min(guest.access_expires_at, conversation.expires_at,
                timezone.now() + timedelta(days=settings.COPILOT_MEMORY_CANDIDATE_DAYS))})
        items.append(item)
    return items
