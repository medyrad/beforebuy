import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CopilotApp } from './CopilotApp'

const conversation = {
  id: '11111111-1111-4111-8111-111111111111', status: 'ACTIVE', title: 'خرید بعدی', brief_revision: 0,
  created_at: '2026-11-15T10:00:00Z', updated_at: '2026-11-15T10:00:00Z', expires_at: '2027-02-13T10:00:00Z',
  brief: { revision: 0, recipient_context: null, category: null, selected_product_label: null, budget_toman: null, use_cases: [], hard_constraints: [], unknowns: [], contradictions: [], confirmed: false, updated_at: '2026-11-15T10:00:00Z' },
  messages: [], operations: [],
}

class FakeEventSource {
  static current: FakeEventSource | null = null
  listeners = new Map<string, (event: MessageEvent<string>) => void>()
  onerror: ((event: Event) => void) | null = null
  constructor(public url: string) { FakeEventSource.current = this }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    this.listeners.set(type, listener as (event: MessageEvent<string>) => void)
  }
  emit(type: string, data = '{}') { this.listeners.get(type)?.(new MessageEvent(type, { data, lastEventId: `op:${type}` })) }
  closed = false
  close() { this.closed = true }
}

describe('Copilot milestone A shell', () => {
  beforeEach(() => {
    vi.stubGlobal('EventSource', FakeEventSource)
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const data = url.endsWith('/session') ? { expires_at: conversation.expires_at }
        : url.endsWith('/messages') && init?.method === 'POST' ? { operation: { id: 'op', status: 'PENDING' }, message_id: 'message', events_url: '/events' }
        : url.endsWith('/cancel') ? { id: 'op', status: 'CANCELLED' }
        : url.endsWith('/operations/op') ? { id: 'op', conversation_id: conversation.id, status: 'RUNNING', expected_brief_revision: 0, final_message_id: null, terminal_code: null }
        : url.includes('/conversations/') ? conversation
        : { items: [conversation], next_cursor: null }
      return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }))
  })

  it('shows Persian fixture disclosure and an honest empty Choice Desk', async () => {
    render(<CopilotApp />)
    expect(await screen.findByRole('heading', { name: 'همراه خرید' })).toBeInTheDocument()
    expect(screen.getByText('بدون AI زنده')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'پیشنهادهای واقعی و منبع‌دار' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'هنوز پیشنهادی بررسی نشده است.' })).toBeInTheDocument()
    expect(screen.queryByText(/قیمت بازار:/)).not.toBeInTheDocument()
  })

  it('preserves explicit mobile conversation and desk controls', async () => {
    const user = userEvent.setup()
    render(<CopilotApp />)
    await screen.findByRole('heading', { name: 'همراه خرید' })
    const desk = screen.getByRole('button', { name: 'میز انتخاب' })
    await user.click(desk)
    await waitFor(() => expect(desk).toHaveClass('active'))
    expect(screen.getByRole('main')).toHaveClass('mobile-active')
  })

  it('offers accessible brief edit and upload controls without later-memory controls', async () => {
    render(<CopilotApp />)
    expect(await screen.findByRole('button', { name: 'ویرایش brief' })).toBeInTheDocument()
    expect(screen.getByLabelText('افزودن تصویر')).toBeInTheDocument()
    expect(screen.queryByText(/حافظه/)).not.toBeInTheDocument()
  })

  it('validates upload size and exposes stop while fixture streaming', async () => {
    const user = userEvent.setup()
    render(<CopilotApp />)
    const input = await screen.findByLabelText('افزودن تصویر') as HTMLInputElement
    await user.upload(input, new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'large.jpg', { type: 'image/jpeg' }))
    expect(screen.getByRole('alert')).toHaveTextContent('حداکثر ۵ مگابایت')
    await user.type(screen.getByRole('textbox', { name: 'پیام شما' }), 'پیام آزمایشی')
    await user.click(screen.getByRole('button', { name: 'ارسال پیام' }))
    FakeEventSource.current?.emit('operation.started')
    expect(await screen.findByRole('button', { name: 'توقف تولید' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'توقف تولید' }))
  })

  it('offers an explicit controlled retry after a terminal fixture failure', async () => {
    const user = userEvent.setup()
    render(<CopilotApp />)
    await user.type(await screen.findByRole('textbox', { name: 'پیام شما' }), 'همان درخواست قبلی')
    await user.click(screen.getByRole('button', { name: 'ارسال پیام' }))
    FakeEventSource.current?.emit('operation.started')
    FakeEventSource.current?.emit('operation.failed', JSON.stringify({ code: 'FIXTURE_FAILURE' }))
    await user.click(await screen.findByRole('button', { name: 'تلاش دوباره' }))
    const messageCalls = vi.mocked(fetch).mock.calls.filter(([input, init]) =>
      String(input).endsWith('/messages') && init?.method === 'POST')
    expect(messageCalls).toHaveLength(2)
  })

  it('reconciles stream errors through REST without regenerating active work', async () => {
    const user = userEvent.setup()
    render(<CopilotApp />)
    await user.type(await screen.findByRole('textbox', { name: 'پیام شما' }), 'پیام reconnect')
    await user.click(screen.getByRole('button', { name: 'ارسال پیام' }))
    FakeEventSource.current?.emit('operation.started')
    FakeEventSource.current?.onerror?.(new Event('error'))
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([input]) => String(input).endsWith('/operations/op'))).toBe(true))
    expect(FakeEventSource.current?.closed).toBe(false)
    const messageCalls = vi.mocked(fetch).mock.calls.filter(([input, init]) =>
      String(input).endsWith('/messages') && init?.method === 'POST')
    expect(messageCalls).toHaveLength(1)
  })

  it('uses REST reconciliation for an in-stream replay gap', async () => {
    const user = userEvent.setup()
    render(<CopilotApp />)
    await user.type(await screen.findByRole('textbox', { name: 'پیام شما' }), 'پیام gap')
    await user.click(screen.getByRole('button', { name: 'ارسال پیام' }))
    FakeEventSource.current?.emit('operation.started')
    FakeEventSource.current?.emit('stream.replay_gap', JSON.stringify({ reconcile_url: '/api/v1/operations/op' }))
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([input]) => String(input).endsWith('/operations/op'))).toBe(true))
    expect(FakeEventSource.current?.closed).toBe(true)
  })

  it('starts exact-url research and renders scoped attributed offers with unknown totals', async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const job = {
        id: 'job-1', conversation_id: conversation.id, operation_id: 'research-op', mode: 'LIVE', fixture_labeled: false,
        status: 'SUCCESS', stage: 'COMPLETED', completed: 1, total: 1, request_count: 1, decoded_bytes: 1000, wire_bytes: 800, redirect_count: 0,
        targets: [{ source_id: 'takkalaban.com', url: 'https://takkalaban.com/product/philips-na230/' }], brief_revision: 0, current_for_brief: true,
        coverage: { extracted: ['takkalaban.com'], blocked: [], failed: [], mode: 'LIVE' }, limits: {}, snapshots: [],
        offers: [{ id: 'offer-1', variant_id: 'variant-1', product_name: 'Philips NA230', seller: 'Takkalaban', source_name: 'takkalaban.com',
          source_url: 'https://takkalaban.com/product/philips-na230/', merchant_url: 'https://takkalaban.com/product/philips-na230/', item_price: 239900000,
          source_currency: 'IRR', price_toman: 23990000, shipping_toman: null, mandatory_charges_toman: null, total_payable_toman: null,
          availability: 'IN_STOCK', observation_kind: 'MERCHANT_PAGE_VERIFIED', evidence_state: 'LIVE', observed_at: '2026-11-15T10:00:00Z',
          fresh_until: '2026-11-15T16:00:00Z' }], created_at: '2026-11-15T10:00:00Z', started_at: '2026-11-15T10:00:00Z', completed_at: '2026-11-15T10:00:01Z',
      }
      const data = url.endsWith('/session') ? { expires_at: conversation.expires_at }
        : url.endsWith('/research') && init?.method === 'POST' ? { job, operation: { id: 'research-op', status: 'COMPLETED' }, idempotent_replay: false, events_url: '/events' }
        : url.endsWith('/research-jobs/job-1') ? job : url.includes('/conversations/') ? conversation : { items: [conversation], next_cursor: null }
      return new Response(JSON.stringify(data), { status: url.endsWith('/research') ? 202 : 200, headers: { 'Content-Type': 'application/json' } })
    })
    render(<CopilotApp />)
    const input = await screen.findByRole('textbox', { name: 'لینک‌های دقیق محصول' })
    await user.type(input, 'https://takkalaban.com/product/philips-na230/')
    await user.click(screen.getByRole('button', { name: 'بررسی پیشنهادها' }))
    expect(await screen.findByText('کمترین قیمت بین منابع بررسی‌شده')).toBeInTheDocument()
    expect(screen.getByText('۲۳٬۹۹۰٬۰۰۰ تومان')).toBeInTheDocument()
    expect(screen.getByText(/هزینهٔ ارسال و مبلغ نهایی نامعلوم/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'مشاهده منبع' })).toHaveAttribute('href', 'https://takkalaban.com/product/philips-na230/')
  })
})
