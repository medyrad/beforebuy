export type ReportMode = 'AI_ASSISTED_SUCCESS' | 'MOCK_ASSISTED' | 'RULE_BASED_LIMITED'

export interface Feedback {
  report_revision_id: string
  report_mode: ReportMode
  rating: number
}

export interface Report {
  report_revision_id: string
  rubric_id: string
  mode: ReportMode
  primary_outcome: string
  dimensions: {
    budget: string
    justification: string
    target_fit: string
    tradeoff: string
  }
  matched_rule_ids: string[]
  evidence: Array<{ id: string; type: string; source_id: string; value: unknown; attribution: string }>
  unknowns: string[]
  actions: string[]
  headline_fa: string
  explanation_blocks: Array<{ text_fa: string; evidence_ids: string[]; rule_ids: string[] }>
  feedback: Feedback | null
}

export interface Analysis {
  id: string
  input_revision: number
  product_label: string
  price_toman: number
  budget_toman: number | null
  answers: Record<string, unknown>
  created_at: string
  expires_at: string
  report: Report
}

export interface AnalysisSummary {
  id: string
  product_label: string
  primary_outcome: string
  mode: ReportMode
  created_at: string
  expires_at: string
}

export interface AnalysisInput {
  product_label: string
  price_toman: string | number
  budget_toman: string | number | null
  answers: Record<string, string | string[]>
}
