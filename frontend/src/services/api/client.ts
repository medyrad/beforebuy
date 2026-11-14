import type { Analysis, AnalysisInput, AnalysisSummary, Feedback } from './types'

interface ErrorEnvelope {
  error?: {
    code?: string
    message?: string
    field_errors?: Record<string, string[]>
  }
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly fieldErrors: Record<string, string[]> = {},
  ) {
    super(message)
  }
}

function cookie(name: string): string | null {
  const prefix = `${name}=`
  const found = document.cookie.split(';').map((item) => item.trim()).find((item) => item.startsWith(prefix))
  return found ? decodeURIComponent(found.slice(prefix.length)) : null
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method?.toUpperCase() ?? 'GET'
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const token = cookie('csrftoken')
    if (token) headers.set('X-CSRFToken', token)
  }
  const response = await fetch(path, { ...init, headers, credentials: 'same-origin' })
  if (!response.ok) {
    let payload: ErrorEnvelope = {}
    try { payload = await response.json() as ErrorEnvelope } catch { /* empty or non-JSON response */ }
    const details = payload.error
    throw new ApiError(
      response.status,
      details?.code ?? 'REQUEST_FAILED',
      details?.message ?? 'ارتباط با سرویس انجام نشد. دوباره تلاش کنید.',
      details?.field_errors ?? {},
    )
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  bootstrap: (signal?: AbortSignal) => request<{ expires_at: string }>('/api/v1/session', { signal }),
  list: (signal?: AbortSignal) => request<{ items: AnalysisSummary[] }>('/api/v1/analyses', { signal }),
  get: (id: string, signal?: AbortSignal) => request<Analysis>(`/api/v1/analyses/${id}`, { signal }),
  create: (input: AnalysisInput) => request<Analysis>('/api/v1/analyses', { method: 'POST', body: JSON.stringify(input) }),
  update: (analysis: Analysis, input: AnalysisInput) => request<Analysis>(`/api/v1/analyses/${analysis.id}`, {
    method: 'PATCH', body: JSON.stringify({ ...input, expected_input_revision: analysis.input_revision }),
  }),
  retry: (analysis: Analysis) => request<Analysis>(`/api/v1/analyses/${analysis.id}/reanalysis`, {
    method: 'POST',
    body: JSON.stringify({
      expected_input_revision: analysis.input_revision,
      expected_report_revision_id: analysis.report.report_revision_id,
    }),
  }),
  delete: (id: string) => request<void>(`/api/v1/analyses/${id}`, { method: 'DELETE' }),
  clear: () => request<{ deleted_count: number }>('/api/v1/analyses/clear', { method: 'POST' }),
  rate: (analysis: Analysis, rating: number) => request<Feedback>(`/api/v1/analyses/${analysis.id}/feedback`, {
    method: 'PUT', body: JSON.stringify({ report_revision_id: analysis.report.report_revision_id, rating }),
  }),
  removeRating: (analysis: Analysis) => request<void>(
    `/api/v1/analyses/${analysis.id}/feedback?report_revision_id=${encodeURIComponent(analysis.report.report_revision_id)}`,
    { method: 'DELETE' },
  ),
}
