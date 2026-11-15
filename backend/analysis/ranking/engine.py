"""Pure categorical comparison; no prose, network or inferred personality input."""
from copy import deepcopy

RULE_VERSION = 'COPILOT-RANK-v0.1'
CRITERIA = {'electronics': {'capacity_gb': int, 'portable': bool},
            'home': {'capacity_l': int, 'dishwasher_safe': bool},
            'sports': {'size_eu': int, 'waterproof': bool}}
ADMISSIBLE = {'VERIFIED_SOURCE', 'SYNTHETIC', 'CAPTURED_FIXTURE'}


def compare(brief, candidates, intended_id):
    profile = brief.get('comparison') or {}
    scope = {'GIFT': 'RECIPIENT', 'HOUSEHOLD': 'HOUSEHOLD'}.get(brief.get('recipient_context'), 'SELF')
    criteria = [c for c in profile.get('criteria', []) if c['scope'] == scope]
    budget = brief.get('budget_toman')
    items = []
    for candidate in candidates[:4]:
        checks, unknowns, tradeoffs = [], [], []
        hard_failed = False
        for criterion in criteria:
            field = criterion['field']; fact = candidate['facts'].get(field, {})
            usable = (fact.get('state') == 'SUPPORTED' and fact.get('attribution') in ADMISSIBLE
                      and fact.get('variant_id') == candidate['id']
                      and type(fact.get('value')) is type(criterion['expected']))
            result = ('SATISFIED' if fact.get('value') == criterion['expected'] else 'FAILED') if usable else 'UNKNOWN'
            checks.append({**criterion, 'result': result, 'actual': fact.get('value') if usable else None,
                           'evidence_id': fact.get('evidence_id'), 'attribution': fact.get('attribution', 'UNKNOWN'),
                           'source_id': fact.get('source_id'), 'source_location': fact.get('source_location')})
            if result == 'UNKNOWN': unknowns.append(field)
            if result == 'FAILED':
                tradeoffs.append(field)
                hard_failed |= criterion['kind'] == 'HARD'
        offers = candidate.get('offers', [])
        fresh_offers = [o for o in offers if o.get('fresh') and o.get('attribution') in ADMISSIBLE]
        in_stock = [o for o in fresh_offers if o['stock'] == 'IN_STOCK']
        out = bool(fresh_offers) and all(o['stock'] == 'OUT_OF_STOCK' for o in fresh_offers)
        if out and candidate['id'] != intended_id: continue
        if out: hard_failed = True; tradeoffs.append('OUT_OF_STOCK')
        if not in_stock and not out: unknowns.append('availability')
        known_totals = [sum(o[k] for k in ('price', 'shipping', 'mandatory')) for o in in_stock
                        if all(type(o.get(k)) is int and o[k] >= 0 for k in ('price', 'shipping', 'mandatory'))]
        prices = [o['price'] for o in in_stock if type(o.get('price')) is int]
        total = min(known_totals) if known_totals else None
        item_price = min(prices) if prices else None
        incomplete_may_fit = budget is not None and any(
            not all(type(o.get(k)) is int and o[k] >= 0 for k in ('price', 'shipping', 'mandatory'))
            and (type(o.get('price')) is not int or o['price'] <= budget) for o in in_stock)
        # A costly complete offer cannot prove that a cheaper incomplete offer is over budget.
        if total is not None and budget is not None and total > budget and incomplete_may_fit:
            total = None
        above = budget is not None and not incomplete_may_fit and ((total is not None and total > budget) or
                                       (total is None and item_price is not None and item_price > budget))
        flexible = profile.get('budget_mode') == 'FLEXIBLE'
        cost_state = 'ABOVE_BUDGET' if above else 'WITHIN_BUDGET_CONFIRMED' if budget is not None and total is not None else 'UNKNOWN'
        if above:
            tradeoffs.append('ABOVE_FLEXIBLE_BUDGET' if flexible else 'ABOVE_STRICT_BUDGET')
            hard_failed |= not flexible
        if total is None: unknowns.append('total_cost')
        if budget is None: unknowns.append('budget')
        unknowns.extend(brief.get('hard_constraints', []))
        if brief.get('contradictions'): unknowns.append('brief_contradiction')
        hard_unknown = (any(c['kind'] == 'HARD' and c['result'] == 'UNKNOWN' for c in checks)
                        or bool(brief.get('hard_constraints')) or bool(brief.get('contradictions'))
                        or total is None or budget is None or (not in_stock and not out))
        group = 'INCOMPATIBLE' if hard_failed else 'UNRESOLVED' if hard_unknown else 'SUPPORTED'
        known = sum(c['result'] != 'UNKNOWN' for c in checks) + int(total is not None) + int(bool(in_stock) or out)
        preference_fit = sum(c['kind'] == 'PREFERENCE' and c['result'] == 'SATISFIED' for c in checks)
        preference_fail = sum(c['kind'] == 'PREFERENCE' and c['result'] == 'FAILED' for c in checks)
        key = ({'SUPPORTED': 0, 'UNRESOLVED': 1, 'INCOMPATIBLE': 2}[group], len(unknowns), -preference_fit, preference_fail,
               (total if total is not None else float('inf')) if profile.get('prefer_lower_cost') else 0)
        items.append({**candidate, 'intended': candidate['id'] == intended_id, 'group': group,
                      'checks': checks, 'unknowns': unknowns, 'tradeoffs': tradeoffs, 'total': total,
                      'item_price': item_price, 'cost_state': cost_state, 'coverage': {'known': known, 'total': len(checks) + 2},
                      'would_change_if': unknowns or ['تغییر نیاز یا شواهد تازه'], '_key': key})
    items.sort(key=lambda item: (item['_key'], item['id']))
    supported = [i for i in items if i['group'] == 'SUPPORTED']
    leaders = [i['id'] for i in supported if i['_key'] == supported[0]['_key']] if supported else []
    outcome = 'TIED' if len(leaders) > 1 else 'SUPPORTED_CHOICE' if leaders else 'UNRESOLVED' if any(
        i['group'] == 'UNRESOLVED' for i in items) else 'NO_SUPPORTED_CHOICE'
    clarification = None
    if budget is None: clarification = 'سقف بودجهٔ این خرید چقدر است؟'
    elif scope == 'RECIPIENT' and not criteria: clarification = 'کدام ویژگی برای گیرندهٔ هدیه مهم‌تر است؟'
    elif items and items[0]['unknowns']:
        field_labels = {'total_cost': 'هزینهٔ نهایی با ارسال', 'availability': 'موجودی',
                        'brief_contradiction': 'تناقض نیاز خرید', 'portable': 'قابل‌حمل بودن',
                        'capacity_gb': 'ظرفیت ذخیره‌سازی', 'capacity_l': 'گنجایش',
                        'dishwasher_safe': 'شست‌وشو در ماشین ظرف‌شویی', 'size_eu': 'سایز کفش', 'waterproof': 'ضدآب بودن'}
        key = items[0]['unknowns'][0]
        clarification = 'برای تصمیم نهایی، «' + field_labels.get(key, key) + '» باید روشن شود.'
    for item in items: item.pop('_key')
    return {'rule_version': RULE_VERSION, 'outcome': outcome, 'leaders': leaders, 'items': items,
            'brief_snapshot': deepcopy(brief),
            'clarification': clarification, 'response_mode': 'DETERMINISTIC_TEMPLATE',
            'intent': profile.get('intent', 'UNKNOWN'), 'scope': scope,
            'no_alternatives': not any(not i['intended'] and i['group'] == 'SUPPORTED' for i in items)}
