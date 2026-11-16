import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { AssistantSettings } from './AssistantSettings'

afterEach(() => vi.unstubAllGlobals())

it('stores only the OpenRouter key without validation and requires explicit synthetic consent', async () => {
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/credential')) return json({ ...credentialFor('openrouter'),
      ...(init?.method === 'PUT' ? { masked: '••••', state: 'STORED_UNVALIDATED' } : {}) })
    return json(settingsFor('openrouter'))
  })
  vi.stubGlobal('fetch', fetcher)
  render(<AssistantSettings />)
  const input = await screen.findByLabelText('کلید OpenRouter')
  fireEvent.change(input, { target: { value: 'synthetic-openrouter-only' } })
  fireEvent.submit(input.closest('form')!)
  await screen.findByText('کلید ذخیره شد؛ اتصال زنده فعال نشده است.')
  expect(fetcher.mock.calls.filter(([url]) => url.includes('/models/refresh'))).toHaveLength(0)
  const put = fetcher.mock.calls.find(([, init]) => init?.method === 'PUT')!
  expect(JSON.parse(String(put[1]?.body)).provider).toBe('openrouter')
  expect(screen.getByRole('button', { name: 'آزمایش رایگان' })).toBeDisabled()
})

it('clears the old key on failed OpenRouter loading and serializes rapid switching', async () => {
  const pending = delayedResponse()
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'PATCH') return pending.promise
    if (url.includes('provider=openrouter')) return new Response('{}', { status: 503 })
    return json(url.includes('/credential') ? { ...credentialFor('gapgpt'), masked: '••••' } : settingsFor('gapgpt'))
  })
  vi.stubGlobal('fetch', fetcher)
  render(<AssistantSettings />)
  fireEvent.change(await screen.findByLabelText('کلید GapGPT'), { target: { value: 'synthetic-old-key' } })
  const select = screen.getByRole('combobox', { name: 'ارائه‌دهنده' })
  act(() => {
    fireEvent.change(select, { target: { value: 'openrouter' } })
    fireEvent.change(select, { target: { value: 'openai' } })
  })
  await act(async () => pending.resolve(json(settingsFor('openrouter'))))
  await screen.findByRole('alert')
  expect(select).toHaveValue('openrouter')
  expect(screen.queryByLabelText('کلید GapGPT')).not.toBeInTheDocument()
  expect(screen.queryByLabelText('کلید OpenRouter')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'حذف کلید' })).not.toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'PATCH')).toHaveLength(1)
})

function delayedResponse() {
  let resolve!: (response: Response) => void
  const promise = new Promise<Response>(done => { resolve = done })
  return { promise, resolve }
}
const json = (value: unknown) => new Response(JSON.stringify(value))
const settingsFor = (provider: string) => ({ provider, revision: 1, memory_enabled: false,
  model: provider + '-model', mode: 'DEMONSTRATION', connection: 'NOT_CONFIGURED',
  catalog: { source: 'DOCUMENTATION_UNVERIFIED', saved_status: 'ACCOUNT_UNVERIFIED', items: [{ id: provider + '-model' }] } })
const credentialFor = (provider: string) => ({ provider, state: 'NOT_CONFIGURED', revision: null,
  encryption_available: true, masked: null, expires_at: null })

it('serializes rapid provider changes, including events before React renders the disabled control', async () => {
  const pending = delayedResponse()
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'PATCH') return pending.promise
    if (url.includes('/credential')) return json(credentialFor(url.includes('openai') ? 'openai' : 'gapgpt'))
    return json(settingsFor('gapgpt'))
  })
  vi.stubGlobal('fetch', fetcher)
  render(<AssistantSettings />)
  await screen.findByLabelText('کلید GapGPT')
  const select = screen.getByRole('combobox', { name: 'ارائه‌دهنده' })
  act(() => {
    fireEvent.change(select, { target: { value: 'openai' } })
    fireEvent.change(select, { target: { value: 'gapgpt' } })
  })
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'PATCH')).toHaveLength(1)
  expect(select).toBeDisabled()
  expect(screen.queryByLabelText('کلید GapGPT')).not.toBeInTheDocument()
  await act(async () => pending.resolve(json(settingsFor('openai'))))
  expect(await screen.findByLabelText('کلید OpenAI')).toBeInTheDocument()
  expect(select).toHaveValue('openai')
})

it('submits a credential once even when two submit events arrive in the same render', async () => {
  const pending = delayedResponse()
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'PUT') return pending.promise
    return json(url.includes('/credential') ? credentialFor('openai') : settingsFor('openai'))
  })
  vi.stubGlobal('fetch', fetcher)
  render(<AssistantSettings />)
  const input = await screen.findByLabelText('کلید OpenAI')
  fireEvent.change(input, { target: { value: 'synthetic-double-submit-only' } })
  const form = input.closest('form')!
  act(() => { fireEvent.submit(form); fireEvent.submit(form) })
  const puts = fetcher.mock.calls.filter(([, init]) => init?.method === 'PUT')
  expect(puts).toHaveLength(1)
  expect(JSON.parse(String(puts[0][1]?.body)).provider).toBe('openai')
  await act(async () => pending.resolve(json(credentialFor('openai'))))
})

it('does not continue an obsolete provider transition after leaving settings', async () => {
  const pending = delayedResponse()
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'PATCH') return pending.promise
    return json(url.includes('/credential') ? credentialFor('gapgpt') : settingsFor('gapgpt'))
  })
  vi.stubGlobal('fetch', fetcher)
  const view = render(<AssistantSettings />)
  await screen.findByLabelText('کلید GapGPT')
  fireEvent.change(screen.getByRole('combobox', { name: 'ارائه‌دهنده' }), { target: { value: 'openai' } })
  view.unmount()
  render(<AssistantSettings />)
  await screen.findByLabelText('کلید GapGPT')
  await act(async () => pending.resolve(json(settingsFor('openai'))))
  expect(fetcher.mock.calls.some(([url]) => url.includes('provider=openai'))).toBe(false)
  expect(screen.getByRole('combobox', { name: 'ارائه‌دهنده' })).toHaveValue('gapgpt')
})

it('deletes only the displayed provider once while rapid clicks and switches are blocked', async () => {
  const pending = delayedResponse()
  let deleted = false
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'DELETE') { deleted = true; return pending.promise }
    if (url.includes('/credential')) return json({ ...credentialFor('openai'),
      ...(deleted ? {} : { masked: '••••', revision: 'openai-revision', state: 'STORED_UNVALIDATED' }) })
    return json(settingsFor('openai'))
  })
  vi.stubGlobal('fetch', fetcher)
  render(<AssistantSettings />)
  const button = await screen.findByRole('button', { name: 'حذف کلید' })
  act(() => { fireEvent.click(button); fireEvent.click(button) })
  const calls = fetcher.mock.calls.filter(([, init]) => init?.method === 'DELETE')
  expect(calls).toHaveLength(1)
  expect(JSON.parse(String(calls[0][1]?.body))).toEqual({ provider: 'openai', expected_revision: 'openai-revision' })
  expect(screen.getByRole('combobox', { name: 'ارائه‌دهنده' })).toBeDisabled()
  await act(async () => pending.resolve(new Response(null, { status: 204 })))
  expect(await screen.findByText('کلیدی ذخیره نشده')).toBeInTheDocument()
  expect(screen.getByLabelText('کلید OpenAI')).toBeInTheDocument()
})
it('never presents the old credential after a partially successful provider switch and can recover', async () => {
  let provider = 'gapgpt'
  let failCredential = true
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/credential')) {
      if (provider === 'openai' && failCredential) return new Response('{}', { status: 503 })
      return new Response(JSON.stringify({ provider, state: 'NOT_CONFIGURED', revision: null, encryption_available: true, masked: null }))
    }
    if (init?.method === 'PATCH') provider = JSON.parse(String(init.body)).provider
    return new Response(JSON.stringify({ provider, revision: provider === 'gapgpt' ? 0 : 1, model: provider + '-model',
      catalog: { items: [{ id: provider + '-model' }], saved_status: 'ACCOUNT_UNVERIFIED' } }))
  })
  vi.stubGlobal('fetch', fetcher)
  const user = userEvent.setup()
  render(<AssistantSettings />)
  await screen.findByLabelText('کلید GapGPT')
  await user.selectOptions(screen.getByLabelText('ارائه‌دهنده'), 'openai')
  await screen.findByRole('alert')
  expect(screen.queryByRole('button', { name: 'ذخیرهٔ کلید' })).not.toBeInTheDocument()
  failCredential = false
  await user.click(screen.getByRole('button', { name: 'بارگذاری دوبارهٔ تنظیمات' }))
  await user.type(await screen.findByLabelText('کلید OpenAI'), 'synthetic-openai-only-key')
  await user.click(screen.getByRole('button', { name: 'ذخیرهٔ کلید' }))
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(true))
  const put = fetcher.mock.calls.find(([, init]) => init?.method === 'PUT')
  expect(JSON.parse(String(put?.[1]?.body))).toMatchObject({ provider: 'openai', expected_revision: null })
})
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

it('labels free-provider onboarding as pending rather than an active connection', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('{}', { status: 503 })))
  render(<AssistantSettings />)
  await userEvent.setup().click(screen.getByText('سهمیهٔ رایگان API — در حال بررسی'))
  expect(screen.getByRole('link', { name: 'ساخت حساب و کلید در OpenRouter' })).toHaveAttribute('href', 'https://openrouter.ai/settings/keys')
  expect(screen.getByText(/فرم مستقل آماده است؛ فعال‌سازی واقعی به شرایط مسیر و حساب بستگی دارد/)).toBeInTheDocument()
  await screen.findByRole('alert')
})
