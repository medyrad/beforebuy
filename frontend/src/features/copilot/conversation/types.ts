export interface Brief {
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
  updated_at: string
}

export interface Message {
  id: string
  role: 'USER' | 'ASSISTANT'
  state: 'ACCEPTED' | 'FINAL' | 'FAILED' | 'CANCELLED'
  text: string
  upload_ids: string[]
  created_at: string
}

export type OperationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'INTERRUPTED'

export interface Operation {
  id: string
  conversation_id: string
  status: OperationStatus
  expected_brief_revision: number
  final_message_id: string | null
  terminal_code: string | null
}

export interface Conversation {
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
