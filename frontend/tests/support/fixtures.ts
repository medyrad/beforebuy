import type { Analysis } from '../../src/services/api/types'

export function analysisFixture(options: { rating?: number } = {}): Analysis {
  return {
    id: '2e0eb18c-20dd-46c4-81bf-0ecb39ec33a2',
    input_revision: 1,
    product_label: 'Phone Model X 256GB',
    price_toman: 45_000_000,
    budget_toman: 50_000_000,
    answers: {},
    created_at: '2026-11-14T08:00:00Z',
    expires_at: '2027-02-12T08:00:00Z',
    report: {
      report_revision_id: 'c64311ce-5902-4626-bbe3-529e20056c9d',
      rubric_id: 'PDA-CAT-v0.3',
      mode: 'MOCK_ASSISTED',
      primary_outcome: 'PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET',
      dimensions: {
        budget: 'WITHIN_BUDGET',
        justification: 'JUSTIFICATION_SUPPORTED',
        target_fit: 'TARGET_FIT_UNVERIFIED',
        tradeoff: 'NOT_REQUIRED',
      },
      matched_rule_ids: ['BUD-01', 'JUS-04', 'FIT-03', 'TRD-03', 'OUT-08'],
      evidence: [],
      unknowns: ['TARGET_MODEL_CAPABILITY'],
      actions: ['VERIFY_TARGET_CAPABILITY'],
      headline_fa: 'خرید یا تعویض گوشی با توجه به وضعیت فعلی قابل توجیه است.',
      explanation_blocks: [],
      feedback: options.rating ? {
        report_revision_id: 'c64311ce-5902-4626-bbe3-529e20056c9d',
        report_mode: 'MOCK_ASSISTED',
        rating: options.rating,
      } : null,
    },
  }
}
