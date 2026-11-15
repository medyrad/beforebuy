from unittest import TestCase


def context():
    return {
        'brief': {'budget_toman': 10_000_000, 'comparison': {'intent': 'ENJOYMENT'}, 'unknowns': []},
        'choice': {'outcome': 'SUPPORTED_CHOICE', 'leaders': ['a'], 'items': [
            {'id': 'a', 'name': 'گزینه آ', 'intended': True, 'group': 'SUPPORTED', 'total': 8_000_000,
             'cost_state': 'WITHIN_BUDGET_CONFIRMED', 'checks': [], 'unknowns': [], 'tradeoffs': [],
             'would_change_if': ['شواهد تازه'], 'coverage': {'known': 2, 'total': 2}, 'sources': []},
            {'id': 'b', 'name': 'گزینه ب', 'intended': False, 'group': 'SUPPORTED', 'total': 9_000_000,
             'cost_state': 'WITHIN_BUDGET_CONFIRMED', 'checks': [
                 {'field': 'portable', 'expected': True, 'actual': False, 'kind': 'PREFERENCE',
                  'result': 'FAILED', 'evidence_id': 'e-b', 'source_id': 's-b', 'attribution': 'SYNTHETIC'},
             ], 'unknowns': [], 'tradeoffs': ['portable'], 'would_change_if': ['شواهد تازه'],
             'coverage': {'known': 3, 'total': 3}, 'sources': [
                 {'id': 's-b', 'attribution': 'SYNTHETIC', 'fresh': True},
             ]},
            {'id': 'c', 'name': 'گزینه پ', 'intended': False, 'group': 'UNRESOLVED', 'total': None,
             'cost_state': 'UNKNOWN', 'checks': [], 'unknowns': ['waterproof'], 'tradeoffs': [],
             'would_change_if': ['waterproof'], 'coverage': {'known': 1, 'total': 3}, 'sources': []},
        ]},
    }


class CopilotAnswerPlanTests(TestCase):
    def test_supported_alternative_and_tradeoff_render_from_authoritative_values(self):
        from analysis.ai.copilot_answer import validate_and_render

        plan = {'answer_type': 'ALTERNATIVES', 'lead_key': 'CURRENT_COMPARISON', 'clarification_key': 'none', 'blocks': [
            {'kind': 'ALTERNATIVE', 'candidate_id': 'b', 'criterion': None, 'evidence_ids': []},
            {'kind': 'TRADEOFF', 'candidate_id': 'b', 'criterion': 'portable', 'evidence_ids': ['e-b']},
        ]}
        rendered = validate_and_render(plan, context())
        self.assertIn('گزینه ب', rendered.final_text)
        self.assertIn('۹٬۰۰۰٬۰۰۰ تومان', rendered.final_text)
        self.assertIn('قابل‌حمل بودن', rendered.final_text)
        self.assertNotIn('بهترین', rendered.final_text)

    def test_unsupported_blocks_become_explicit_limited_explanation(self):
        from analysis.ai.copilot_answer import validate_and_render

        plan = {'answer_type': 'COMPARISON_ANSWER', 'lead_key': 'CURRENT_COMPARISON',
                'clarification_key': 'none', 'blocks': [
                    {'kind': 'MISMATCH', 'candidate_id': 'a', 'criterion': 'made_up',
                     'evidence_ids': ['not-current']},
                ]}
        rendered = validate_and_render(plan, context())
        self.assertEqual(rendered.supported_blocks, 0)
        self.assertIn('شاهد کافی', rendered.final_text)
        self.assertNotIn('made_up', rendered.final_text)

    def test_unknown_comparison_is_guidance_not_an_invented_claim(self):
        from analysis.ai.copilot_answer import validate_and_render

        plan = {'answer_type': 'UNKNOWN_GUIDANCE', 'lead_key': 'LIMITED_EVIDENCE',
                'clarification_key': 'none', 'blocks': [
                    {'kind': 'UNKNOWN', 'candidate_id': 'c', 'criterion': 'waterproof', 'evidence_ids': []},
                    {'kind': 'NEXT_CHECK', 'candidate_id': 'c', 'criterion': 'waterproof', 'evidence_ids': []},
                ]}
        rendered = validate_and_render(plan, context())
        self.assertIn('نامعلوم', rendered.final_text)
        self.assertIn('بررسی', rendered.final_text)
        self.assertNotIn('ضدآب است', rendered.final_text)

    def test_budget_clarification_is_rejected_when_budget_is_already_known(self):
        from analysis.ai.copilot_answer import AnswerPlanError, validate_and_render

        plan = {'answer_type': 'CLARIFICATION', 'lead_key': 'CURRENT_COMPARISON',
                'clarification_key': 'budget_toman', 'blocks': []}
        with self.assertRaisesRegex(AnswerPlanError, 'UNSUPPORTED_CLARIFICATION'):
            validate_and_render(plan, context())

    def test_more_than_three_alternatives_is_rejected(self):
        from analysis.ai.copilot_answer import AnswerPlanError, validate_and_render

        plan = {'answer_type': 'ALTERNATIVES', 'lead_key': 'CURRENT_COMPARISON',
                'clarification_key': 'none', 'blocks': [
                    {'kind': 'ALTERNATIVE', 'candidate_id': str(index), 'criterion': None, 'evidence_ids': []}
                    for index in range(4)
                ]}
        with self.assertRaisesRegex(AnswerPlanError, 'MALFORMED_PLAN'):
            validate_and_render(plan, context())
