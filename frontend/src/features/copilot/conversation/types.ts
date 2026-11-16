export interface Brief {
  conversation_state?: { pending_budget?: { budget_toman: number; source_message_id: string } }
  revision: number
  recipient_context: 'SELF' | 'GIFT' | 'HOUSEHOLD' | null
  category: string | null
  selected_product_label: string | null
  budget_toman: number | null
  use_cases: string[]
  hard_constraints: string[]
  unknowns: string[]
  contradictions: string[]
  confirmed: boolean
  comparison?: {
    intent?: string; budget_mode?: string; prefer_lower_cost?: boolean
    criteria?: { field: string; expected: number | boolean; kind: string; scope: string }[]
  }
  updated_at: string
}

export interface Message {
  reply_actions?: ReplyAction[]
  id: string
  role: 'USER' | 'ASSISTANT'
  state: 'ACCEPTED' | 'FINAL' | 'FAILED' | 'CANCELLED'
  text: string
  upload_ids: string[]
  created_at: string
}

export type OperationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'INTERRUPTED'

export interface Operation {
  operation_kind?: string
  id: string
  conversation_id: string
  status: OperationStatus
  expected_brief_revision: number
  final_message_id: string | null
  terminal_code: string | null
}

export interface Conversation {
  openrouter_pilot?: boolean
  messages_truncated?: boolean
  temporary?: boolean
  id: string
  status: 'ACTIVE'
  title: string
  brief_revision: number
  created_at: string
  updated_at: string
  expires_at: string
  brief: Brief
  messages: Message[]
  operations: Operation[]
}

export interface ReplyAction {
  id: string; label: string; kind: string; value: string | null
  conversation_id: string; question_id: string; revision: number
}
export interface Answer { question_id: string; action_id: string; revision: number }

export type ConversationSummary = Omit<Conversation, 'brief' | 'messages' | 'operations'>

export interface Upload {
  id: string
  conversation_id: string
  media_type: string
  size_bytes: number
  width: number
  height: number
  expires_at: string
}

export interface ResearchOffer {
  id: string; variant_id: string; product_name: string; seller: string | null; source_name: string
  source_url: string | null; merchant_url: string | null; item_price: number | null; source_currency: string | null
  price_toman: number | null; shipping_toman: number | null; mandatory_charges_toman: number | null
  total_payable_toman: number | null; warranty: string | null
  availability: 'IN_STOCK' | 'OUT_OF_STOCK' | 'PREORDER' | 'UNKNOWN'
  observation_kind: 'COMPARISON_OBSERVED' | 'MERCHANT_PAGE_VERIFIED'
  evidence_state: 'LIVE' | 'CACHE' | 'STALE' | 'CAPTURED_FIXTURE' | 'SYNTHETIC'; observed_at: string; fresh_until: string
}

export interface ResearchJob {
  id: string; status: string; stage: string; completed: number; total: number; request_count: number
  coverage: { extracted?: string[]; blocked?: { source_id: string; code: string }[]; failed?: { source_id: string; code: string }[]; mode?: string }
  offers: ResearchOffer[]
}
