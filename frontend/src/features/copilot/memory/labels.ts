import type { Memory } from './api'
import { labels } from '../choice-desk/labels'
const scopes: Record<string, string> = { SELF: 'خودم', RECIPIENT: 'گیرندهٔ هدیه', HOUSEHOLD: 'خانه' }
export function preferenceLabel(item: Memory) {
  return `${labels[item.criterion.field]}: ${typeof item.criterion.expected === 'boolean' ? item.criterion.expected ? 'بله' : 'خیر' : item.criterion.expected.toLocaleString('fa-IR')} — ${scopes[item.criterion.scope]}`
}
