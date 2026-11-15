import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { AssistantSettings } from './AssistantSettings'

afterEach(() => vi.unstubAllGlobals())
it('shows blocked account-unverified settings and clears the synthetic credential after save', async () => {
  let saved = false
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/credential')) {
      if (init?.method === 'PUT') saved = true
      return new Response(JSON.stringify({ state: saved ? 'STORED_UNVALIDATED' : 'NOT_CONFIGURED', revision: saved ? 'r' : null,
        encryption_available: true, masked: saved ? '••••••••' : null, validation: 'UNAVAILABLE_BLOCKED' }))
    }
    return new Response(JSON.stringify({ memory_enabled: false, revision: 0, model: 'gpt-6-luna',
      catalog: { source: 'DOCUMENTATION_UNVERIFIED', saved_status: 'ACCOUNT_UNVERIFIED', items: [{ id: 'gpt-6-luna' }] } }))
  })
  vi.stubGlobal('fetch', fetcher)
  const user = userEvent.setup()
  render(<AssistantSettings />)
  const input = await screen.findByLabelText('کلید OpenAI')
  expect(input).toHaveAttribute('type', 'password')
  expect(screen.getByText(/اشتراک ChatGPT/)).toBeInTheDocument()
  expect(screen.getByText(/ایران/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'بررسی صریح مدل‌های حساب' })).toBeInTheDocument()
  expect(fetcher.mock.calls.some(([url]) => url.endsWith('/models/refresh'))).toBe(false)
  await user.type(input, 'synthetic-test-only-123456')
  await user.click(screen.getByRole('button', { name: 'ذخیرهٔ کلید' }))
  await waitFor(() => expect(input).toHaveValue(''))
  expect(await screen.findByText('ذخیره‌شده؛ اعتبارسنجی نشده')).toBeInTheDocument()
  expect(screen.queryByText('synthetic-test-only-123456')).not.toBeInTheDocument()
  expect(fetcher.mock.calls.every(([url]) => url.startsWith('/api/v1/copilot/'))).toBe(true)
})
