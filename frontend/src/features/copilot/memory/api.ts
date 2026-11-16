import { call } from '../conversation/api'
import type { Brief } from '../conversation/types'
export type Criterion = NonNullable<NonNullable<Brief['comparison']>['criteria']>[number]
export interface Memory { id: string; category: string; criterion: Criterion; state: string; revision: number; expires_at: string }
export interface ModelCatalog { source: string; saved_status: string; items: { id: string }[] }
export interface Settings { memory_enabled: boolean; provider: 'gapgpt' | 'openai' | 'openrouter'; model: string; revision: number; mode: string; connection: string; credential_state?: string; catalog: ModelCatalog;
  openrouter?: { service_eligible: boolean; route_eligible: boolean; data_consent: boolean; account_verified: boolean; remaining_attempts: number; blocked: boolean } }
export interface Credential { provider: string; state: string; revision: string | null; encryption_available: boolean; masked: string | null; expires_at: string | null }
const root = '/api/v1/copilot'
const write = (method: string, data: unknown) => ({ method, body: JSON.stringify(data) })
export const memoryApi = {
  settings: () => call<Settings>(`${root}/settings`),
  update: (data: unknown) => call<Settings>(`${root}/settings`, write('PATCH', data)),
  refreshModels: () => call<ModelCatalog>(`${root}/models/refresh`, write('POST', {})),
  freePilot: () => call<ModelCatalog & { conversation_id: string }>(`${root}/models/refresh`, write('POST', { synthetic_consent: true })),
  credential: (provider: string) => call<Credential>(`${root}/credential?provider=${encodeURIComponent(provider)}`),
  saveKey: (provider: string, key: string, revision: string | null) => call<Credential>(`${root}/credential`, write('PUT', { provider, key, expected_revision: revision })),
  deleteKey: (provider: string, revision: string | null) => call<void>(`${root}/credential`, write('DELETE', { provider, expected_revision: revision })),
  list: () => call<{ items: Memory[] }>(`${root}/memory`),
  edit: (id: string, data: unknown) => call<Memory>(`${root}/memory/${id}`, write('PATCH', data)),
  remove: (id?: string) => call<void>(`${root}/memory${id ? '/' + id : ''}`, { method: 'DELETE' }),
  suggestions: (id: string) => call<{ items: Memory[] }>(`/api/v1/conversations/${id}/memory`),
  propose: (id: string, revision: number) => call<{ items: Memory[] }>(`/api/v1/conversations/${id}/memory`, write('POST', { expected_revision: revision })),
  apply: (id: string, revision: number, memory: Memory) => call<Brief>(`/api/v1/conversations/${id}/memory`, write('PATCH', { expected_revision: revision, memory_id: memory.id, memory_revision: memory.revision })),
}
export const failureText = (reason: unknown) => reason instanceof Error ? reason.message : 'درخواست انجام نشد؛ دوباره تلاش کنید.'
