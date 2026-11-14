import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Questionnaire } from '../src/features/analysis/Questionnaire'
import { buildSubmission, createEmptyDraft, deriveFollowUps, validateMoney } from '../src/features/analysis/draft'

describe('جریان پرسش‌نامه', () => {
  it('مبلغ گروه‌بندی‌شده با رقم فارسی را معتبر می‌داند', () => {
    expect(validateMoney('۱۲٬۵۰۰٬۰۰۰', false)).toBeNull()
  })

  it('ریشهٔ فارسی و RTL، labelهای تومان و حفظ ورودی در خطا را ارائه می‌کند', async () => {
    const user = userEvent.setup()
    render(<Questionnaire initialDraft={createEmptyDraft()} onCancel={vi.fn()} onSubmit={vi.fn()} />)

    expect(document.documentElement).toHaveAttribute('lang', 'fa')
    expect(document.documentElement).toHaveAttribute('dir', 'rtl')
    await user.type(screen.getByRole('textbox', { name: /چه تلفنی/ }), 'مدل نمونه')
    const price = screen.getByRole('textbox', { name: /قیمت تقریبی.*تومان/ })
    await user.type(price, '۱۲,۵۰,۰۰۰')
    await user.click(screen.getByRole('button', { name: 'ادامه' }))
    expect(price).toHaveValue('۱۲,۵۰,۰۰۰')
    expect(screen.getByRole('alert')).toHaveTextContent('فرمت مبلغ')
    expect(price).toHaveFocus()
  })

  it('بودجهٔ صفر و نامعلوم را متمایز نگه می‌دارد و follow-upها را به سه محدود می‌کند', () => {
    const draft = createEmptyDraft()
    draft.q001 = 'SERIOUS_PROBLEM'
    draft.q002 = 'UNKNOWN'
    draft.q003 = ['GAMING', 'ACCESSIBILITY', 'WORK_STUDY']
    draft.q004 = 'UNKNOWN'
    draft.q006 = ['NONE']
    draft.budgetKind = 'zero'
    draft.f002 = 'SOLVE_MAJOR_LIMIT'

    expect(deriveFollowUps(draft)).toEqual(['F-001', 'F-002', 'F-003'])
    const zero = buildSubmission(draft)
    expect(zero.budget_toman).toBe(0)
    expect(zero.answers['Q-002']).toBe('SOLVE_MAJOR_LIMIT')

    draft.budgetKind = 'unknown'
    expect(buildSubmission(draft).budget_toman).toBeNull()
  })
})
