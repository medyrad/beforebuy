"""Validate model-selected answer blocks against authoritative context."""
from dataclasses import dataclass


class AnswerPlanError(ValueError):
    pass


@dataclass(frozen=True)
class RenderedAnswer:
    final_text: str
    chunks: tuple[str, ...]
    supported_blocks: int


def validate_and_render(plan, context, *, allow_empty=False):
    _validate_shape(plan)
    if plan['clarification_key'] != 'none':
        question = _clarification(plan['clarification_key'], context.get('brief') or {})
        return RenderedAnswer(question, (question,), 0)
    choice = context.get('choice') or {}
    items = {item.get('id'): item for item in choice.get('items', []) if isinstance(item, dict)}
    chunks = []
    for block in plan['blocks']:
        candidate = items.get(block['candidate_id'])
        rendered = _render_block(block, candidate)
        if rendered:
            chunks.append(rendered)
    if not chunks and allow_empty:
        return RenderedAnswer('', (), 0)
    if not chunks:
        limited = 'برای این بخش از پاسخ، شاهد کافی و معتبر در مقایسهٔ فعلی ندارم.'
        return RenderedAnswer(limited, (limited,), 0)
    final = ' '.join(chunks)
    return RenderedAnswer(final, tuple(chunks), len(chunks))


def validate_conversational_plan(payload, context):
    """Allow natural needs dialogue while keeping every factual block server-owned."""
    import re
    if not isinstance(payload, dict) or set(payload) != {'conversation', 'answer_plan'}:
        raise AnswerPlanError('MALFORMED_PLAN')
    conversation = payload['conversation']
    if not isinstance(conversation, dict) or set(conversation) != {
        'acknowledgement', 'next_question', 'brief_proposal'
    }:
        raise AnswerPlanError('MALFORMED_PLAN')
    acknowledgement = conversation['acknowledgement']
    question = conversation['next_question']
    proposal = conversation['brief_proposal']
    if not isinstance(acknowledgement, str) or not 1 <= len(acknowledgement.strip()) <= 300:
        raise AnswerPlanError('MALFORMED_PLAN')
    if question is not None and (not isinstance(question, str) or not 1 <= len(question.strip()) <= 220
                                 or not question.rstrip().endswith(('؟', '?'))):
        raise AnswerPlanError('MALFORMED_PLAN')
    texts = [acknowledgement] + ([] if question is None else [question])
    source_text = ' '.join([context.get('current_message', '')] + [
        item.get('text', '') for item in (context.get('history') or {}).get('items', []) if isinstance(item, dict)
    ])
    source_digits = set(re.findall(r'\d+', _ascii_digits(source_text)))
    forbidden = ('http://', 'https://', 'قیمت امروز', 'قیمت فعلی', 'موجود است', 'ناموجود است', 'تومان', 'ریال', 'دلار')
    for text in texts:
        normalized = _ascii_digits(text)
        if any(value in text for value in forbidden):
            raise AnswerPlanError('UNSUPPORTED_CONVERSATION_CLAIM')
        if any(value not in source_digits for value in re.findall(r'\d+', normalized)):
            raise AnswerPlanError('UNSUPPORTED_CONVERSATION_CLAIM')
    factual = validate_and_render(payload['answer_plan'], context, allow_empty=True)
    chunks = [acknowledgement.strip()]
    if proposal:
        from rest_framework.exceptions import ValidationError
        from analysis.conversation.brief import validate_brief_changes
        try:
            clean = validate_brief_changes(proposal)
        except ValidationError:
            raise AnswerPlanError('MALFORMED_PLAN') from None
        labels = {
            'recipient_context': 'مخاطب', 'category': 'دسته', 'selected_product_label': 'محصول',
            'budget_toman': 'بودجه', 'use_cases': 'کاربردها', 'hard_constraints': 'الزام‌ها',
        }
        values = []
        for key, value in clean.items():
            if key not in labels:
                raise AnswerPlanError('MALFORMED_PLAN')
            shown = '، '.join(value) if isinstance(value, list) else str(value)
            values.append(f'{labels[key]}: {shown}')
        chunks.append('پیشنهاد برای تأیید نیاز خرید: ' + '؛ '.join(values) + '. این تغییر هنوز اعمال نشده است.')
    chunks.extend(factual.chunks)
    if question:
        chunks.append(question.strip())
    return RenderedAnswer(' '.join(chunks), tuple(chunks), factual.supported_blocks)


def _ascii_digits(value):
    return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))


def safe_lead(context):
    if context.get('choice'):
        return 'مقایسهٔ فعلی را فقط بر پایهٔ شواهد معتبر و نیاز ثبت‌شده بررسی می‌کنم. '
    return 'برای پاسخ دقیق‌تر، وضعیت نیاز ثبت‌شده را بررسی می‌کنم. '


def _validate_shape(plan):
    if not isinstance(plan, dict) or set(plan) != {'answer_type', 'lead_key', 'clarification_key', 'blocks'}:
        raise AnswerPlanError('MALFORMED_PLAN')
    if plan['answer_type'] not in {'COMPARISON_ANSWER', 'ALTERNATIVES', 'UNKNOWN_GUIDANCE', 'CLARIFICATION'}:
        raise AnswerPlanError('MALFORMED_PLAN')
    if plan['lead_key'] not in {'CURRENT_COMPARISON', 'LIMITED_EVIDENCE', 'NEEDS_CONTEXT'}:
        raise AnswerPlanError('MALFORMED_PLAN')
    if plan['clarification_key'] not in {'none', 'budget_toman', 'category', 'recipient_context', 'use_cases'}:
        raise AnswerPlanError('MALFORMED_PLAN')
    if not isinstance(plan['blocks'], list) or len(plan['blocks']) > 3:
        raise AnswerPlanError('MALFORMED_PLAN')
    if sum(block.get('kind') == 'ALTERNATIVE' for block in plan['blocks'] if isinstance(block, dict)) > 3:
        raise AnswerPlanError('MALFORMED_PLAN')
    for block in plan['blocks']:
        if not isinstance(block, dict) or set(block) != {'kind', 'candidate_id', 'criterion', 'evidence_ids'}:
            raise AnswerPlanError('MALFORMED_PLAN')
        if block['kind'] not in {'ALTERNATIVE', 'TRADEOFF', 'MISMATCH', 'UNKNOWN', 'NEXT_CHECK'}:
            raise AnswerPlanError('MALFORMED_PLAN')
        if not isinstance(block['candidate_id'], str) or not isinstance(block['evidence_ids'], list):
            raise AnswerPlanError('MALFORMED_PLAN')
        if block['criterion'] is not None and not isinstance(block['criterion'], str):
            raise AnswerPlanError('MALFORMED_PLAN')
        if not all(isinstance(value, str) for value in block['evidence_ids']):
            raise AnswerPlanError('MALFORMED_PLAN')


def _render_block(block, candidate):
    if not candidate:
        return None
    kind = block['kind']
    criterion = block['criterion']
    evidence = set(block['evidence_ids'])
    checks = [item for item in candidate.get('checks', []) if item.get('field') == criterion]
    admissible = {'VERIFIED_SOURCE', 'SYNTHETIC', 'CAPTURED_FIXTURE'}
    sources = {item.get('id'): item for item in candidate.get('sources', [])
               if item.get('fresh') and item.get('attribution') in admissible}
    matching = {item.get('evidence_id') for item in checks
                if item.get('evidence_id') and item.get('attribution') in admissible
                and item.get('source_id') in sources
                and sources[item.get('source_id')].get('attribution') == item.get('attribution')}
    name = candidate.get('name') or 'این گزینه'
    if kind == 'ALTERNATIVE':
        if candidate.get('intended') or candidate.get('group') != 'SUPPORTED' or evidence:
            return None
        total = candidate.get('total')
        cost = f' هزینهٔ نهایی ثبت‌شدهٔ آن {_toman(total)} است.' if type(total) is int else ''
        return f'«{name}» یک جایگزین پشتیبانی‌شده در مقایسهٔ فعلی است.{cost}'
    if kind in {'TRADEOFF', 'MISMATCH'}:
        failed = any(item.get('result') == 'FAILED' for item in checks)
        if not criterion or not failed or not evidence or not evidence.issubset(matching):
            return None
        if kind == 'TRADEOFF' and criterion not in candidate.get('tradeoffs', []):
            return None
        return f'دربارهٔ «{name}»، {_criterion(criterion)} با نیاز ثبت‌شده هم‌خوان نیست و یک بده‌بستان است.'
    if kind == 'UNKNOWN':
        if evidence or criterion not in candidate.get('unknowns', []):
            return None
        return f'دربارهٔ «{name}»، {_criterion(criterion)} هنوز نامعلوم است.'
    if kind == 'NEXT_CHECK':
        if evidence or criterion not in candidate.get('would_change_if', []):
            return None
        return f'پیش از تصمیم، {_criterion(criterion)} را از منبع معتبر بررسی کنید.'
    return None


def _clarification(key, brief):
    values = {
        'budget_toman': brief.get('budget_toman'),
        'category': brief.get('category'),
        'recipient_context': brief.get('recipient_context'),
        'use_cases': brief.get('use_cases'),
    }
    if values[key] is not None and values[key] != [] and values[key] != '':
        raise AnswerPlanError('UNSUPPORTED_CLARIFICATION')
    return {
        'budget_toman': 'سقف بودجهٔ این خرید چقدر است؟',
        'category': 'چه دسته‌ای از محصول را بررسی می‌کنید؟',
        'recipient_context': 'این خرید برای خودتان، هدیه یا خانه است؟',
        'use_cases': 'کاربرد اصلی این خرید چیست؟',
    }[key]


def _criterion(value):
    return {
        'portable': 'قابل‌حمل بودن', 'capacity_gb': 'ظرفیت ذخیره‌سازی',
        'capacity_l': 'گنجایش', 'dishwasher_safe': 'قابلیت شست‌وشو در ماشین ظرف‌شویی',
        'size_eu': 'سایز', 'waterproof': 'ضدآب بودن', 'total_cost': 'هزینهٔ نهایی',
        'availability': 'موجودی', 'budget': 'بودجه',
    }.get(value, 'این معیار')


def _toman(value):
    digits = str(f'{value:,}').translate(str.maketrans('0123456789,', '۰۱۲۳۴۵۶۷۸۹٬'))
    return digits + ' تومان'
