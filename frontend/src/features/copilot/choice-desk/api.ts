import { call } from '../conversation/api'

export interface Source {
  id: string; attribution: string; label: string; url?: string | null; fresh: boolean; observed_at: string; fresh_until: string
}
export interface Candidate {
  id: string; name: string; category: string; sources: Source[]
  offers: { id: string; seller: string; price: number | null; shipping: number | null; mandatory: number | null; stock: string; fresh: boolean; attribution: string; source_id: string; url: string | null; observation_kind: string; observed_at: string }[]
}
export interface ChoiceItem extends Candidate {
  intended: boolean; group: string; total: number | null; item_price: number | null; cost_state: string
  checks: { field: string; expected: boolean | number; actual: boolean | number | null; kind: string; scope: string; result: string; evidence_id: string | null; attribution: string }[]
  unknowns: string[]; tradeoffs: string[]; coverage: { known: number; total: number }; would_change_if: string[]
}
export interface Choice {
  id: string; brief_revision: number; current: boolean
  evidence_valid_until?: string
  result: { outcome: string; items: ChoiceItem[]; leaders: string[]; intent: string; no_alternatives: boolean; clarification: string | null }
}
const path = (id: string) => `/api/v1/conversations/${id}/choices`
export const choiceApi = {
  get: (id: string) => call<Choice | null>(path(id)),
  candidates: (id: string) => call<{ items: Candidate[] }>(path(id) + '/candidates'),
  demo: (id: string, revision: number, category: string) => call<{ variant_ids: string[] }>(path(id) + '/demo', { method: 'POST', body: JSON.stringify({ expected_revision: revision, category }) }),
  compare: (id: string, revision: number, ids: string[], intended: string) => call<Choice>(path(id), { method: 'POST', body: JSON.stringify({ expected_revision: revision, variant_ids: ids, intended_variant_id: intended }) }),
}
