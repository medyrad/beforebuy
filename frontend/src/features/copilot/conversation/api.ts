import type { Brief, Conversation, ConversationSummary, Operation, Upload } from './types'

export class CopilotApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message) }
}

function csrfCookie() {
  const item = document.cookie.split(';').map((part) => part.trim()).find((part) => part.startsWith('csrftoken='))
  return item ? decodeURIComponent(item.slice('csrftoken='.length)) : ''
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const method = (init.method ?? 'GET').toUpperCase()
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRFToken', csrfCookie())
  const response = await fetch(path, { ...init, headers, credentials: 'same-origin' })
  if (!response.ok) {
    const data = await response.json().catch(() => ({})) as { error?: { code?: string; message?: string }; code?: string; detail?: string }
    throw new CopilotApiError(response.status, data.error?.code ?? data.code ?? 'REQUEST_FAILED', data.error?.message ?? data.detail ?? 'درخواست انجام نشد.')
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const copilotApi = {
  bootstrap: () => call<{ expires_at: string }>('/api/v1/session'),
  list: () => call<{ items: ConversationSummary[]; next_cursor: string | null }>('/api/v1/conversations?limit=50'),
  create: () => call<Conversation>('/api/v1/conversations', { method: 'POST', body: '{}' }),
  get: (id: string) => call<Conversation>(`/api/v1/conversations/${id}`),
  remove: (id: string) => call<void>(`/api/v1/conversations/${id}`, { method: 'DELETE' }),
  editBrief: (id: string, expectedRevision: number, changes: Record<string, unknown>) => call<Brief>(`/api/v1/conversations/${id}/brief`, {
    method: 'PATCH', body: JSON.stringify({ expected_revision: expectedRevision, changes }),
  }),
  confirmBrief: (id: string, expectedRevision: number) => call<Brief>(`/api/v1/conversations/${id}/brief/confirm`, {
    method: 'POST', body: JSON.stringify({ expected_revision: expectedRevision }),
  }),
  send: (id: string, text: string, revision: number, uploadIds: string[], key: string) => call<{ operation: Operation; message_id: string; events_url: string }>(`/api/v1/conversations/${id}/messages`, {
    method: 'POST', headers: { 'Idempotency-Key': key },
    body: JSON.stringify({ text, expected_brief_revision: revision, upload_ids: uploadIds }),
  }),
  cancel: (id: string) => call<Operation>(`/api/v1/operations/${id}/cancel`, { method: 'POST', body: '{}' }),
  operation: (id: string) => call<Operation>(`/api/v1/operations/${id}`),
  upload: (conversationId: string, image: File) => {
    const body = new FormData(); body.set('conversation_id', conversationId); body.set('image', image)
    return call<Upload>('/api/v1/uploads', { method: 'POST', body })
  },
}

export function newIdempotencyKey() {
  return `web-${crypto.randomUUID()}`
}
