from copy import deepcopy
from itertools import permutations
from unittest import TestCase
from tests.unit.test_copilot_ranking import candidate, brief
from analysis.ranking.engine import compare


class RankingInvariants(TestCase):
    def test_input_order_and_prose_cannot_change_order(self):
        values = [candidate('c'), candidate('a'), candidate('b')]
        for order in permutations(values):
            result = compare(brief(), list(order), 'c')
            self.assertEqual([i['id'] for i in result['items']], ['a', 'b', 'c'])
            self.assertEqual(result['outcome'], 'TIED')
        altered = deepcopy(values)
        for item in altered:
            item['name'] = 'متن تبلیغاتی'; item['facts']['unsupported'] = {'value': 999}
        self.assertEqual([i['id'] for i in compare(brief(), altered, 'c')['items']], ['a', 'b', 'c'])

    def test_removing_evidence_never_improves_coverage(self):
        b = brief(); b['comparison']['criteria'] = [{'field': 'portable', 'expected': True, 'kind': 'HARD', 'scope': 'SELF'}]
        supported = compare(b, [candidate(portable=True)], 'a')['items'][0]
        unknown = compare(b, [candidate()], 'a')['items'][0]
        self.assertGreater(supported['coverage']['known'], unknown['coverage']['known'])
        self.assertEqual(unknown['group'], 'UNRESOLVED')
