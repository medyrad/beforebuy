import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { MemoryPanel } from './MemoryPanel'

it('keeps consent off until explicit action and separates candidate from confirmed', async () => {
  let enabled = false
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/settings')) {
      if (init?.method === 'PATCH') enabled = true
      return new Response(JSON.stringify({ memory_enabled: enabled, revision: 0 }))
    }
    return new Response(JSON.stringify({ items: enabled ? [{ id: 'm', category: 'electronics', revision: 0,
      state: 'CANDIDATE', criterion: { field: 'portable', expected: true, kind: 'PREFERENCE', scope: 'RECIPIENT' },
      expires_at: '2027-01-01T00:00:00Z' }] : [] }))
  }))
  const user = userEvent.setup(); render(<MemoryPanel />)
  await user.click(await screen.findByRole('button', { name: 'فعال‌کردن حافظه با رضایت من' }))
  expect(await screen.findByText('پیشنهاد؛ منتظر تأیید')).toBeInTheDocument()
  expect(screen.getByText(/گیرندهٔ هدیه/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'تأیید ترجیح' })).toBeInTheDocument()
  vi.unstubAllGlobals()
})
