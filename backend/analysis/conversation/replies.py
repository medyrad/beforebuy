"""Explicit bounded answer grammar; not general language understanding."""
import re
from decimal import Decimal

CONFIRM = 'تأیید تغییر بودجه'
KEEP = 'همان بودجهٔ قبلی'
NEED = 'نیاز خرید را تأیید می‌کنم'
RECIPIENTS = [('برای خودم', 'SELF'), ('برای هدیه', 'GIFT'), ('برای خانه', 'HOUSEHOLD')]
CATEGORIES = [('کالای دیجیتال', 'electronics'), ('لوازم خانه', 'home'),
              ('پوشاک و ورزش', 'sports'), ('سایر خریدها', 'other')]
QUESTIONS = {'category': 'چه دسته‌ای از محصول را بررسی می‌کنید؟',
             'recipient_context': 'این خرید برای خودتان، هدیه یا خانه است؟'}


def explicit_budget(text):
    normalized = text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬', '01234567890123456789.,')).strip()
    # Only an explicit budget statement or a standalone amount; never a product price/range.
    pattern = r'(?:بودجه(?:[‌ ]?ام)?\s*[:،]?\s*)?([0-9]+(?:[.,][0-9]+)*)\s*(هزار|میلیون)?\s*(تومان|ریال)(?:\s+است)?[.!؟]?'
    match = re.fullmatch(pattern, normalized)
    if not match:
        return None
    raw, scale, unit = match.groups()
    if ',' in raw and not re.fullmatch(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', raw):
        return None
    value = Decimal(raw.replace(',', '')) * {'هزار': 1000, 'میلیون': 1_000_000, None: 1}[scale]
    if unit == 'ریال':
        value /= 10
    if value != value.to_integral_value() or not 0 <= value <= 10**12:
        return None
    return int(value)


def validate_action(conversation, text, answer):
    from .operations import OperationConflict
    latest = conversation.messages.order_by('-created_at', '-id').first()
    current_question = bool(latest and latest.role == 'ASSISTANT'
                            and latest.created_at >= conversation.brief.updated_at)
    if answer is None:
        return next((a for a in (latest.reply_actions if current_question else [])
                     if a['label'] == text and a['revision'] == conversation.brief_revision), None)
    if not isinstance(answer, dict) or set(answer) != {'question_id', 'action_id', 'revision'} or type(answer['revision']) is not int:
        raise OperationConflict('INVALID_ANSWER', 'پاسخ انتخابی نامعتبر است.')
    if (not current_question or str(latest.id) != answer['question_id']
            or answer['revision'] != conversation.brief_revision):
        raise OperationConflict('STALE_ANSWER', 'این پرسش تغییر کرده است؛ آخرین پیام را پاسخ دهید.')
    action = next((a for a in latest.reply_actions if a['id'] == answer['action_id']
                   and a['revision'] == answer['revision'] and a['label'] == text), None)
    if action is None:
        raise OperationConflict('STALE_ANSWER', 'این پاسخ دیگر قابل انتخاب نیست.')
    return action


def apply_explicit_answer(conversation, message, action):
    brief = conversation.brief
    changes = {}
    state = dict(brief.conversation_state)
    pending = state.get('pending_budget')
    kind = action['kind'] if action else None
    if kind == 'CONFIRM_BUDGET' and pending:
        changes['budget_toman'] = pending['budget_toman']
        state = {}
    elif kind == 'KEEP_BUDGET':
        state = {}
    elif kind == 'SET_CATEGORY':
        changes['category'] = action['value']
    elif kind == 'SET_RECIPIENT':
        changes['recipient_context'] = action['value']
    elif kind == 'CONFIRM_NEED':
        brief.confirmed = True
    elif kind == 'CORRECT_NEED':
        state = {'correcting_need': True}
    else:
        amount = explicit_budget(message.text)
        if amount is not None:
            if brief.budget_toman is None or amount == brief.budget_toman:
                changes['budget_toman'] = amount
                state = {}
            else:
                state = {'pending_budget': {'budget_toman': amount, 'source_message_id': str(message.id)}}
        if state.get('correcting_need'):
            for prefix, field in [('دسته:', 'category'), ('کاربرد:', 'use_cases')]:
                if message.text.startswith(prefix) and 0 < len(message.text[len(prefix):].strip()) <= 120:
                    value = message.text[len(prefix):].strip()
                    changes[field] = [value] if field == 'use_cases' else dict(CATEGORIES).get(value, value)
                    state = {}
        # Free text answers to the server-owned category/recipient/use question, not global keyword NLP.
        previous = conversation.messages.exclude(id=message.id).order_by('-created_at', '-id').first()
        if (previous and previous.role == 'ASSISTANT' and previous.created_at >= brief.updated_at
                and amount is None and not pending):
            if QUESTIONS['category'] in previous.text and len(message.text) <= 120:
                changes['category'] = dict(CATEGORIES).get(message.text, message.text)
            elif QUESTIONS['recipient_context'] in previous.text and message.text in dict(RECIPIENTS):
                changes['recipient_context'] = dict(RECIPIENTS)[message.text]
            elif 'کاربرد اصلی این خرید چیست؟' in previous.text and len(message.text) <= 200:
                changes['use_cases'] = [message.text]
    if changes or state != brief.conversation_state or kind == 'CONFIRM_NEED':
        for field, value in changes.items():
            setattr(brief, field, value)
        brief.conversation_state = state
        if kind != 'CONFIRM_NEED':
            brief.confirmed = False
        brief.provenance = [*brief.provenance, *[{'field': field, 'source_type': 'USER_REPORTED',
                            'source_id': str(message.id)} for field in changes]]
        standard = {'بودجه': brief.budget_toman is None, 'دستهٔ محصول': not brief.category,
                    'مخاطب خرید': not brief.recipient_context, 'کاربرد اصلی': not brief.use_cases}
        brief.unknowns = [v for v in brief.unknowns if v not in standard] + [k for k, v in standard.items() if v]
        brief.revision += 1
        brief.save()
        conversation.brief_revision = brief.revision
        conversation.generation_epoch += 1
        conversation.save(update_fields=['brief_revision', 'generation_epoch', 'updated_at'])


def local_question(brief):
    """Only deterministic clarification of explicit state; no product claims."""
    pending = brief.get('conversation_state', {}).get('pending_budget')
    if brief.get('conversation_state', {}).get('correcting_need'):
        return 'چه چیزی را اصلاح کنیم؟ بودجه را با مبلغ و واحد، دسته را با «دسته: …» یا کاربرد را با «کاربرد: …» بنویسید. این نسخه فقط همین پاسخ‌های مشخص را ثبت می‌کند.'
    if pending:
        def money(value):
            return f'{value:,}'.translate(str.maketrans('0123456789,', '۰۱۲۳۴۵۶۷۸۹٬'))
        return (f'بودجهٔ گفته‌شدهٔ قبلی {money(brief["budget_toman"])} تومان است. '
                f'مبلغ جدید برابر {money(pending["budget_toman"])} تومان است (۱۰ ریال = ۱ تومان). '
                'این تغییر بودجه را تأیید می‌کنید؟')
    if (brief.get('budget_toman') is not None and brief.get('category') and brief.get('recipient_context')
            and brief.get('use_cases') and not brief.get('confirmed')):
        return 'برداشت از نیاز خرید شما در میز انتخاب آمده است. آن را تأیید می‌کنید یا می‌خواهید اصلاحش کنید؟'
    return None


def actions_for(final, brief):
    options = []
    if brief.conversation_state.get('pending_budget'):
        options = [(CONFIRM, 'CONFIRM_BUDGET', None), (KEEP, 'KEEP_BUDGET', None)]
    elif QUESTIONS['category'] in final.text:
        options = [(label, 'SET_CATEGORY', value) for label, value in CATEGORIES]
    elif QUESTIONS['recipient_context'] in final.text:
        options = [(label, 'SET_RECIPIENT', value) for label, value in RECIPIENTS]
    elif 'برداشت از نیاز خرید شما' in final.text:
        options = [(NEED, 'CONFIRM_NEED', None), ('می‌خواهم اصلاح کنم', 'CORRECT_NEED', None)]
    return [{'id': f'answer-{index}', 'label': label, 'kind': kind, 'value': value,
             'conversation_id': str(final.conversation_id), 'question_id': str(final.id), 'revision': brief.revision}
            for index, (label, kind, value) in enumerate(options)]
