import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { CopilotApp } from './CopilotApp'

afterEach(() => vi.unstubAllGlobals())
it('allows a first message without a preliminary create click and reports backend mode', async () => {
  const c = { id: 'c', brief_revision: 0, messages: [], operations: [], brief: {
    revision: 0, confirmed: false, budget_toman: null, use_cases: [], unknowns: [], contradictions: [], hard_constraints: [] } }
  vi.stubGlobal('EventSource', class { addEventListener() {} close() {} })
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const data = url.endsWith('/settings') ? { provider: 'openai', model: 'gpt-6-luna', mode: 'DEMONSTRATION', connection: 'STORED_UNVALIDATED' }
      : url.endsWith('/messages') ? { operation: { id: 'o', status: 'PENDING' }, events_url: '/events' }
      : url === '/api/v1/conversations' && init?.method === 'POST' ? c
      : url.endsWith('/c') ? c : { items: [], next_cursor: null }
    return new Response(JSON.stringify(data), { status: 200 })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<CopilotApp />)
  expect(await screen.findByRole('heading', { name: 'برای چه خریدی کمکت کنم؟' })).toBeInTheDocument()
  const input = screen.getByRole('textbox', { name: 'پیام شما' })
  await waitFor(() => expect(input).toBeEnabled())
  await userEvent.type(input, 'برای خانه یک صندلی می‌خواهم')
  await userEvent.click(screen.getByRole('button', { name: 'ارسال پیام' }))
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/messages'))).toBe(true))
  expect(fetcher.mock.calls.filter(([url, init]) => url === '/api/v1/conversations' && init?.method === 'POST')).toHaveLength(1)
  expect(screen.getByText('نسخهٔ نمایشی')).toBeInTheDocument()
})
