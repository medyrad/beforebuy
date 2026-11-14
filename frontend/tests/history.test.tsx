import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { HistoryView } from '../src/features/history/HistoryView'

describe('تاریخچه', () => {
  it('حالت خالی و توضیح دسترسی همان مرورگر را نشان می‌دهد', () => {
    render(<HistoryView items={[]} loading={false} error={null} onOpen={vi.fn()} onDelete={vi.fn()} onClear={vi.fn()} />)
    expect(screen.getByText('هنوز تحلیلی ندارید')).toBeVisible()
    expect(screen.getByText(/همین مرورگر/)).toBeVisible()
  })

  it('پاک‌کردن همه را فقط پس از تأیید اجرا می‌کند', async () => {
    const user = userEvent.setup()
    const onClear = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<HistoryView items={[{ id: 'a', product_label: 'مدل نمونه', primary_outcome: 'INSUFFICIENT_CONTEXT', mode: 'MOCK_ASSISTED', created_at: '2026-11-14T08:00:00Z', expires_at: '2027-02-12T08:00:00Z' }]} loading={false} error={null} onOpen={vi.fn()} onDelete={vi.fn()} onClear={onClear} />)
    await user.click(screen.getByRole('button', { name: 'پاک‌کردن همهٔ تاریخچه' }))
    expect(onClear).toHaveBeenCalledOnce()
  })
})
