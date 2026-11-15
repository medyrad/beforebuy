"""Validate model-selected answer blocks against authoritative context."""
from dataclasses import dataclass


class AnswerPlanError(ValueError):
    pass


@dataclass(frozen=True)
class RenderedAnswer:
    final_text: str
    chunks: tuple[str, ...]
    supported_blocks: int


def validate_and_render(plan, context):
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
    if not chunks:
        limited = 'برای این بخش از پاسخ، شاهد کافی و معتبر در مقایسهٔ فعلی ندارم.'
        return RenderedAnswer(limited, (limited,), 0)
    final = ' '.join(chunks)
    return RenderedAnswer(final, tuple(chunks), len(chunks))


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
    if values[key]:
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
