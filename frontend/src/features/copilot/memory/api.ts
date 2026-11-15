import { call } from '../conversation/api'
import type { Brief } from '../conversation/types'
export type Criterion = NonNullable<NonNullable<Brief['comparison']>['criteria']>[number]
export interface Memory { id: string; category: string; criterion: Criterion; state: string; revision: number; expires_at: string }
export interface Settings { memory_enabled: boolean; model: string; revision: number; catalog: { saved_status: string; items: { id: string }[] } }
export interface Credential { state: string; revision: string | null; encryption_available: boolean; masked: string | null; expires_at: string | null }
const root = '/api/v1/copilot'
const write = (method: string, data: unknown) => ({ method, body: JSON.stringify(data) })
export const memoryApi = {
  settings: () => call<Settings>(`${root}/settings`),
  update: (data: unknown) => call<Settings>(`${root}/settings`, write('PATCH', data)),
  credential: () => call<Credential>(`${root}/credential`),
  saveKey: (key: string, revision: string | null) => call<Credential>(`${root}/credential`, write('PUT', { key, expected_revision: revision })),
  deleteKey: (revision: string | null) => call<void>(`${root}/credential`, write('DELETE', { expected_revision: revision })),
  list: () => call<{ items: Memory[] }>(`${root}/memory`),
  edit: (id: string, data: unknown) => call<Memory>(`${root}/memory/${id}`, write('PATCH', data)),
  remove: (id?: string) => call<void>(`${root}/memory${id ? '/' + id : ''}`, { method: 'DELETE' }),
  suggestions: (id: string) => call<{ items: Memory[] }>(`/api/v1/conversations/${id}/memory`),
  propose: (id: string, revision: number) => call<{ items: Memory[] }>(`/api/v1/conversations/${id}/memory`, write('POST', { expected_revision: revision })),
  apply: (id: string, revision: number, memory: Memory) => call<Brief>(`/api/v1/conversations/${id}/memory`, write('PATCH', { expected_revision: revision, memory_id: memory.id, memory_revision: memory.revision })),
}
export const failureText = (reason: unknown) => reason instanceof Error ? reason.message : 'درخواست انجام نشد؛ دوباره تلاش کنید.'
