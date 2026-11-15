from copy import deepcopy
from unittest import TestCase
from analysis.ranking.engine import compare


def candidate(identifier='a', price=80, shipping=0, **facts):
    return {'id': identifier, 'name': identifier, 'facts': {
        k: {'value': v, 'state': 'SUPPORTED', 'attribution': 'SYNTHETIC', 'variant_id': identifier,
            'evidence_id': k} for k, v in facts.items()},
        'offers': [{'price': price, 'shipping': shipping, 'mandatory': 0, 'stock': 'IN_STOCK',
                    'fresh': True, 'id': identifier, 'attribution': 'SYNTHETIC'}], 'sources': [], 'category': 'electronics'}


def brief(**changes):
    return {'budget_toman': 100, 'recipient_context': 'SELF', 'hard_constraints': [],
            'comparison': {'intent': 'PRACTICAL', 'budget_mode': 'STRICT', 'criteria': []}, **changes}


class RankingCases(TestCase):
    def test_practical_and_enjoyment_are_equally_valid(self):
        for intent in ['PRACTICAL', 'ENJOYMENT', 'HOUSEHOLD', 'GIFT']:
            b = brief(); b['comparison']['intent'] = intent
            self.assertEqual(compare(b, [candidate()], 'a')['items'][0]['group'], 'SUPPORTED')

    def test_budget_boundaries_unknown_shipping_and_flexible_tradeoff(self):
        for item, expected in [(candidate(price=100), 'SUPPORTED'), (candidate(price=101), 'INCOMPATIBLE'),
                               (candidate(shipping=None), 'UNRESOLVED')]:
            self.assertEqual(compare(brief(), [item], 'a')['items'][0]['group'], expected)
        b = brief(); b['comparison']['budget_mode'] = 'FLEXIBLE'
        result = compare(b, [candidate(price=101)], 'a')['items'][0]
        self.assertEqual(result['group'], 'SUPPORTED')
        self.assertIn('ABOVE_FLEXIBLE_BUDGET', result['tradeoffs'])

    def test_hard_failure_unknown_supported_and_variant_mismatch(self):
        b = brief(); b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'HARD', 'scope': 'SELF'}]
        for item, expected in [(candidate(portable=False), 'INCOMPATIBLE'), (candidate(), 'UNRESOLVED'),
                               (candidate(portable=True), 'SUPPORTED')]:
            self.assertEqual(compare(b, [item], 'a')['items'][0]['group'], expected)
        item = candidate(portable=True); item['facts']['portable']['variant_id'] = 'other'
        self.assertEqual(compare(b, [item], 'a')['items'][0]['group'], 'UNRESOLVED')

    def test_gift_uses_recipient_not_purchaser_preferences(self):
        b = brief(recipient_context='GIFT')
        b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'HARD', 'scope': 'SELF'}]
        result = compare(b, [candidate(portable=False)], 'a')
        self.assertEqual(result['items'][0]['checks'], [])
        self.assertIsNotNone(result['clarification'])

    def test_stale_conflicting_and_unsupported_facts_are_unknown(self):
        b = brief(); b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'HARD', 'scope': 'SELF'}]
        for state in ['STALE', 'CONFLICTING', 'UNKNOWN']:
            item = candidate(portable=True); item['facts']['portable']['state'] = state
            self.assertEqual(compare(b, [item], 'a')['items'][0]['group'], 'UNRESOLVED')
        item = candidate(portable=True); item['facts']['portable']['attribution'] = 'ASSISTANT_INFERENCE'
        self.assertEqual(compare(b, [item], 'a')['items'][0]['group'], 'UNRESOLVED')

    def test_sparse_evidence_ties_and_no_alternatives(self):
        b = brief(); b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'PREFERENCE', 'scope': 'SELF'}]
        result = compare(b, [candidate('b'), candidate('a', portable=True)], 'b')
        self.assertEqual(result['items'][0]['id'], 'a')
        self.assertEqual(compare(brief(), [candidate('b'), candidate('a')], 'b')['outcome'], 'TIED')
        self.assertEqual(compare(brief(), [candidate(price=200)], 'a')['outcome'], 'NO_SUPPORTED_CHOICE')

    def test_stock_and_unknown_budget(self):
        c = candidate('b'); c['offers'][0]['stock'] = 'OUT_OF_STOCK'
        self.assertEqual(len(compare(brief(), [candidate(), c], 'a')['items']), 1)
        self.assertEqual(compare(brief(budget_toman=None), [candidate()], 'a')['items'][0]['group'], 'UNRESOLVED')

    def test_unsupported_offer_and_wrong_fact_type_do_not_contribute(self):
        c = candidate(); c['offers'][0]['attribution'] = 'ASSISTANT_INFERENCE'
        self.assertEqual(compare(brief(), [c], 'a')['items'][0]['group'], 'UNRESOLVED')
        b = brief(); b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'HARD', 'scope': 'SELF'}]
        self.assertEqual(compare(b, [candidate(portable=1)], 'a')['items'][0]['checks'][0]['result'], 'UNKNOWN')

    def test_contradictory_brief_cannot_produce_supported_winner(self):
        self.assertEqual(compare(brief(contradictions=['incompatible requirements']), [candidate()], 'a')['outcome'], 'UNRESOLVED')

    def test_incomplete_cheaper_offer_is_not_proven_over_budget(self):
        c = candidate(price=120)
        c['offers'].append(candidate('other', price=80, shipping=None)['offers'][0])
        item = compare(brief(), [c], 'a')['items'][0]
        self.assertEqual(item['group'], 'UNRESOLVED')
        self.assertEqual(item['cost_state'], 'UNKNOWN')
        self.assertIsNone(item['total'])
