import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { ChoiceDesk } from './ChoiceDesk'
import { choiceApi } from './api'
import type { Conversation } from '../conversation/types'

vi.mock('./api', () => ({ choiceApi: { get: vi.fn(), candidates: vi.fn(), demo: vi.fn(), compare: vi.fn() } }))
const conversation = { id: 'c', brief_revision: 1, brief: { confirmed: true, category: 'electronics', comparison: {} } } as Conversation
const item = { id: 'v', name: 'رایانهٔ فارسی Example X با نام بلند برای بررسی خوانایی', category: 'electronics', intended: true, group: 'UNRESOLVED',
  sources: [{ id: 's', attribution: 'CAPTURED_FIXTURE', label: 'ثبت تاریخی', fresh: false, observed_at: '2026-01-01T00:00:00Z', fresh_until: '2026-01-02T00:00:00Z' }],
  offers: [], checks: [], unknowns: ['total_cost'], tradeoffs: [], total: null, item_price: 8000000, coverage: { known: 1, total: 2 }, would_change_if: ['total_cost'] }
const choice = { id: 'choice', brief_revision: 1, current: true, result: { items: [item], outcome: 'UNRESOLVED', leaders: [], intent: 'ENJOYMENT', no_alternatives: true, clarification: null } }
beforeEach(() => {
  vi.mocked(choiceApi.get).mockResolvedValue(choice as never)
  vi.mocked(choiceApi.candidates).mockResolvedValue({ items: [item] } as never)
})
it('labels template and historical evidence, preserves unknown cost and exposes source disclosure', async () => {
  const user = userEvent.setup(); render(<ChoiceDesk conversation={conversation} />)
  expect(await screen.findByText('اطلاعات برای تصمیم قطعی کافی نیست')).toBeInTheDocument()
  expect(screen.getByText(/پاسخ قالبی و قطعی/)).toBeInTheDocument()
  expect(screen.getAllByText(/هزینهٔ نهایی/).length).toBeGreaterThan(0)
  expect(screen.getByText(/جایگزین پشتیبانی‌شده‌ای/)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /شواهد و منابع/ }))
  expect(screen.getByRole('dialog')).toHaveTextContent('ثبت واقعیِ تاریخی')
  await user.tab()
  expect(screen.getByRole('button', { name: 'بستن منابع' })).toHaveFocus()
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})
it('invalidates an old comparison immediately after a brief edit and never shows a final winner', async () => {
  const { rerender } = render(<ChoiceDesk conversation={conversation} />)
  await screen.findByText('اطلاعات برای تصمیم قطعی کافی نیست')
  rerender(<ChoiceDesk conversation={{ ...conversation, brief_revision: 2, brief: { ...conversation.brief, confirmed: false } }} />)
  expect(screen.getByRole('status')).toHaveTextContent('مقایسهٔ قبلی معتبر نیست')
  expect(screen.queryByText('اطلاعات برای تصمیم قطعی کافی نیست')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'ساخت مقایسه' })).toBeDisabled()
})

it('discards a comparison response arriving after a consequential edit', async () => {
  let release!: (value: never) => void
  vi.mocked(choiceApi.compare).mockReturnValue(new Promise((resolve) => { release = resolve }))
  const user = userEvent.setup()
  const { rerender } = render(<ChoiceDesk conversation={conversation} />)
  await waitFor(() => expect(screen.getByRole('button', { name: 'ساخت مقایسه' })).toBeEnabled())
  await user.click(screen.getByRole('button', { name: 'ساخت مقایسه' }))
  rerender(<ChoiceDesk conversation={{ ...conversation, brief_revision: 2, brief: { ...conversation.brief, confirmed: false } }} />)
  await act(async () => release({ ...choice, result: { ...choice.result, outcome: 'SUPPORTED_CHOICE' } } as never))
  expect(screen.queryByText('یک انتخاب با پشتوانهٔ نیازهای معلوم')).not.toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('مقایسهٔ قبلی معتبر نیست')
})
