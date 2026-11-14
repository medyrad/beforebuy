import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ReportView } from '../src/features/analysis/ReportView'
import { analysisFixture } from './support/fixtures'

describe('گزارش تحلیل', () => {
  it('نتیجه، ابعاد مستقل، نامعلومی مدل و برچسب mock را بدون enum خام نشان می‌دهد', () => {
    render(<ReportView analysis={analysisFixture()} onEdit={vi.fn()} onRetry={vi.fn()} onRate={vi.fn()} onRemoveRating={vi.fn()} pendingAction={null} />)
    expect(screen.getByRole('status')).toHaveTextContent('نسخهٔ نمایشی')
    expect(screen.getByText('مناسب‌بودن مدل')).toBeVisible()
    expect(screen.getByText(/مشخصات فنی این مدل تأیید نشده/)).toBeVisible()
    expect(screen.queryByText('TARGET_FIT_UNVERIFIED')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'جمع‌بندی برای تصمیم شما' })).toBeVisible()
    expect(screen.queryByText('هر بُعد، یک پاسخ مستقل')).not.toBeInTheDocument()
  })

  it('feedback را ثبت و حذف‌پذیر می‌کند', async () => {
    const user = userEvent.setup()
    const onRate = vi.fn()
    const onRemove = vi.fn()
    const value = analysisFixture({ rating: 4 })
    render(<ReportView analysis={value} onEdit={vi.fn()} onRetry={vi.fn()} onRate={onRate} onRemoveRating={onRemove} pendingAction={null} />)
    await user.click(screen.getByRole('radio', { name: '۵، خیلی کمک کرد' }))
    expect(onRate).toHaveBeenCalledWith(5)
    await user.click(screen.getByRole('button', { name: 'حذف امتیاز' }))
    expect(onRemove).toHaveBeenCalled()
  })

  it('دو سر طیف امتیاز را برای screen reader توضیح می‌دهد', () => {
    render(<ReportView analysis={analysisFixture()} onEdit={vi.fn()} onRetry={vi.fn()} onRate={vi.fn()} onRemoveRating={vi.fn()} pendingAction={null} />)
    expect(screen.getByRole('radio', { name: '۱، اصلاً کمک نکرد' })).toBeVisible()
    expect(screen.getByRole('radio', { name: '۵، خیلی کمک کرد' })).toBeVisible()
    expect(screen.getByText('اصلاً کمک نکرد')).toBeVisible()
    expect(screen.getByText('خیلی کمک کرد')).toBeVisible()
  })
})
