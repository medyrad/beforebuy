import type { Analysis, AnalysisInput } from '../../services/api/types'

export type BudgetKind = 'amount' | 'zero' | 'unknown'
export type FollowUpId = 'F-001' | 'F-002' | 'F-003'

export interface Draft {
  productLabel: string
  price: string
  budget: string
  budgetKind: BudgetKind
  q001: string
  q002: string
  q003: string[]
  q004: string
  q006: string[]
  f001: string
  f002: string
  f003: string
}

const contradictions = new Set([
  'WORKS_WELL|RESTORE_ESSENTIAL_ACCESS', 'WORKS_WELL|SOLVE_MAJOR_LIMIT',
  'MINOR_PROBLEM|RESTORE_ESSENTIAL_ACCESS', 'MINOR_PROBLEM|SOLVE_MAJOR_LIMIT',
  'NO_DEVICE|SOLVE_MINOR_LIMIT',
])

export function createEmptyDraft(): Draft {
  return {
    productLabel: '', price: '', budget: '', budgetKind: 'amount',
    q001: '', q002: '', q003: [], q004: '', q006: [], f001: '', f002: '', f003: '',
  }
}

export function deriveFollowUps(draft: Draft): FollowUpId[] {
  const candidates: FollowUpId[] = []
  if (draft.q001 === 'SERIOUS_PROBLEM' || contradictions.has(`${draft.q001}|${draft.q002}`)) candidates.push('F-001')
  if (draft.q002 === 'UNKNOWN') candidates.push('F-002')
  if (draft.q003.some((item) => ['GAMING', 'ACCESSIBILITY', 'WORK_STUDY'].includes(item))) candidates.push('F-003')
  return candidates.slice(0, 3)
}

export function buildSubmission(draft: Draft): AnalysisInput {
  const followUps = deriveFollowUps(draft)
  const resolvedBenefit = followUps.includes('F-002') && draft.f002 && draft.f002 !== 'STILL_UNKNOWN'
    ? draft.f002 : draft.q002
  const answers: Record<string, string | string[]> = {
    'Q-001': draft.q001,
    'Q-002': resolvedBenefit,
    'Q-003': draft.q003,
    'Q-004': draft.q004,
    'Q-006': draft.q006,
  }
  if (followUps.includes('F-001') && draft.f001.trim()) answers['F-001'] = draft.f001.trim()
  if (followUps.includes('F-002') && draft.f002) answers['F-002'] = draft.f002
  if (followUps.includes('F-003')) answers['F-003'] = draft.f003 || 'NO_INFORMATION'
  return {
    product_label: draft.productLabel.trim(),
    price_toman: draft.price,
    budget_toman: draft.budgetKind === 'unknown' ? null : draft.budgetKind === 'zero' ? 0 : draft.budget,
    answers,
  }
}

export function draftFromAnalysis(analysis: Analysis): Draft {
  const answer = (key: string) => analysis.answers[key]
  return {
    productLabel: analysis.product_label,
    price: String(analysis.price_toman),
    budget: analysis.budget_toman && analysis.budget_toman > 0 ? String(analysis.budget_toman) : '',
    budgetKind: analysis.budget_toman === null ? 'unknown' : analysis.budget_toman === 0 ? 'zero' : 'amount',
    q001: String(answer('Q-001') ?? ''), q002: String(answer('Q-002') ?? ''),
    q003: Array.isArray(answer('Q-003')) ? answer('Q-003') as string[] : [],
    q004: String(answer('Q-004') ?? ''),
    q006: Array.isArray(answer('Q-006')) ? answer('Q-006') as string[] : [],
    f001: String(answer('F-001') ?? ''), f002: String(answer('F-002') ?? ''), f003: String(answer('F-003') ?? ''),
  }
}

const digits = '[0-9۰-۹]'
const plain = new RegExp(`^${digits}+$`)
const grouped = new RegExp(`^${digits}{1,3}([,٬ ]${digits}{3})+$`)

export function validateMoney(value: string, allowZero: boolean): string | null {
  const trimmed = value.trim()
  if (!trimmed) return 'این مبلغ الزامی است.'
  if (/[eE]/.test(trimmed)) return 'نمایش علمی مثل 1e7 پشتیبانی نمی‌شود؛ رقم کامل تومان را وارد کنید.'
  if (/[.٫]/.test(trimmed)) return 'مبلغ اعشاری پشتیبانی نمی‌شود؛ مبلغ را به تومان و به‌صورت عدد صحیح وارد کنید.'
  if (/\p{L}/u.test(trimmed)) return 'واحد این جریان تومان است؛ فقط مبلغ را به تومان وارد کنید.'
  if (!plain.test(trimmed) && !grouped.test(trimmed)) return 'فرمت مبلغ قابل تشخیص نیست؛ نمونه معتبر: ۱۲٬۵۰۰٬۰۰۰ تومان.'
  const normalized = trimmed.replace(/[۰-۹]/g, (character) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(character))).replace(/[,٬ ]/g, '')
  if (!allowZero && BigInt(normalized) === 0n) return 'قیمت خرید باید بزرگ‌تر از صفر تومان باشد.'
  return null
}
