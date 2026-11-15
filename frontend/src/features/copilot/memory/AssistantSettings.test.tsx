import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { AssistantSettings } from './AssistantSettings'

afterEach(() => vi.unstubAllGlobals())
it('shows selected GapGPT path, stores its key separately, and makes no implicit validation call', async () => {
  let saved = false
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/credential')) {
      if (!init?.method) expect(url).toContain('provider=gapgpt')
      if (init?.method === 'PUT') saved = true
      return new Response(JSON.stringify({ provider: 'gapgpt', state: saved ? 'STORED_UNVALIDATED' : 'NOT_CONFIGURED', revision: saved ? 'r' : null,
        encryption_available: true, masked: saved ? '••••••••' : null, validation: 'UNAVAILABLE_BLOCKED' }))
    }
    return new Response(JSON.stringify({ memory_enabled: false, revision: 0, provider: 'gapgpt',
      model: 'gapgpt-deepseek-v4.1-flash', mode: 'DEMONSTRATION', connection: 'NOT_CONFIGURED',
      catalog: { source: 'DOCUMENTATION_UNVERIFIED', saved_status: 'ACCOUNT_UNVERIFIED',
        items: [{ id: 'gapgpt-deepseek-v4.1-flash' }] } }))
  })
  vi.stubGlobal('fetch', fetcher)
  const user = userEvent.setup()
  render(<AssistantSettings />)
  const input = await screen.findByLabelText('کلید GapGPT')
  expect(input).toHaveAttribute('type', 'password')
  expect(screen.getByText(/میزبانی‌شده در ایران/)).toBeInTheDocument()
  expect(screen.getAllByText(/OpenAI قدیمی/).length).toBeGreaterThan(0)
  expect(screen.getByRole('button', { name: 'بررسی صریح مدل‌های حساب' })).toBeInTheDocument()
  expect(fetcher.mock.calls.some(([url]) => url.endsWith('/models/refresh'))).toBe(false)
  await user.type(input, 'synthetic-test-only-123456')
  await user.click(screen.getByRole('button', { name: 'ذخیرهٔ کلید' }))
  await waitFor(() => expect(input).toHaveValue(''))
  expect(await screen.findByText('ذخیره‌شده؛ اعتبارسنجی نشده')).toBeInTheDocument()
  expect(screen.queryByText('synthetic-test-only-123456')).not.toBeInTheDocument()
  const put = fetcher.mock.calls.find(([url, init]) => url.includes('/credential') && init?.method === 'PUT')
  expect(String(put?.[1]?.body)).toContain('"provider":"gapgpt"')
  expect(fetcher.mock.calls.every(([url]) => url.startsWith('/api/v1/copilot/'))).toBe(true)
})
