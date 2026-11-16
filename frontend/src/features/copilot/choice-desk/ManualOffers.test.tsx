import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { ManualOffers, ObservedOffers } from './ManualOffers'
import { choiceApi } from './api'
import type { Candidate } from './api'
vi.mock('./api', () => ({ choiceApi: { manual: vi.fn() } }))

it('excludes stale, conflicting and unavailable offers from minima without hiding their observations', () => {
  const observation = { seller: 'آزمون', price: 100, shipping: null, mandatory: null, stock: 'IN_STOCK',
    fresh: true, attribution: 'USER_REPORTED', source_id: 's', url: null, observation_kind: 'USER_REPORTED', observed_at: '2026-11-16T10:00:00Z' }
  const candidate: Candidate = { id: 'v', name: 'محصول مصنوعی', category: 'electronics',
    sources: [{ id: 's', attribution: 'USER_REPORTED', label: 'manual', fresh: true, observed_at: observation.observed_at, fresh_until: observation.observed_at }],
    offers: [{ ...observation, id: '1', conflicting: true }, { ...observation, id: '2', fresh: false },
      { ...observation, id: '3', stock: 'OUT_OF_STOCK' }, { ...observation, id: '4', price: 500, total: 550 }] }
  render(<ObservedOffers candidates={[candidate]} />)
  expect(screen.getByText(/کمترین قیمت کالای موجود/)).toHaveTextContent('۵۰۰ تومان؛ کمترین مبلغ نهایی با اجزای معلوم: ۵۵۰ تومان')
  expect(screen.getByText(/مشاهدات این فروشنده تعارض دارند/)).toBeVisible()
  expect(screen.getByText(/قدیمی — برای قیمت فعلی بررسی شود/)).toBeVisible()
  expect(screen.getAllByText('واردشده توسط کاربر؛ مستقلاً تأیید نشده')).toHaveLength(4)
})

it('submits explicit units and observation, then clears seller fields without a technical recommendation', async () => {
  vi.mocked(choiceApi.manual).mockResolvedValue({ variant_id: 'v', offer_id: 'o', attribution: 'USER_REPORTED' })
  const refresh = vi.fn(); const user = userEvent.setup()
  render(<ManualOffers conversationId="c" revision={1} category="electronics" candidates={[]} onSaved={refresh} />)
  await user.click(screen.getByText('ثبت پیشنهادی که خودم دیده‌ام'))
  for (const [label, value] of [['برند', 'Test'], ['نام دقیق محصول', 'TV'], ['کد مدل سازنده', 'TV-55'],
    ['فروشنده', 'فروشگاه آزمون'], ['لینک صفحهٔ پیشنهاد', 'https://merchant.example/product/tv'], ['قیمت مشاهده‌شده', '۱۵۰۰۰۰۰۰۰']]) {
    await user.type(screen.getByLabelText(label, { exact: true }), value)
  }
  await user.selectOptions(screen.getByLabelText('واحد مبلغ اصلی'), 'IRR')
  await user.type(screen.getByLabelText('زمان مشاهدهٔ شما'), '2026-01-01T12:00')
  await user.click(screen.getByRole('button', { name: 'ثبت پیشنهاد دستی' }))
  await waitFor(() => expect(refresh).toHaveBeenCalledWith('v'))
  expect(choiceApi.manual).toHaveBeenCalledWith('c', expect.objectContaining({ currency: 'IRR', amount: '۱۵۰۰۰۰۰۰۰', shipping_toman: null, mandatory_toman: null }))
  expect(screen.getByLabelText('فروشنده', { exact: true })).toHaveValue('')
  expect(screen.getAllByText(/واردشده توسط کاربر؛ مستقلاً تأیید نشده/).length).toBeGreaterThan(0)
})
