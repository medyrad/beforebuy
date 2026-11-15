import { useEffect, useState } from 'react'
import type { Conversation } from '../conversation/types'
import { memoryApi, failureText } from './api'
import type { Memory } from './api'
import { preferenceLabel } from './labels'

export function MemorySuggestions({ conversation, onSaved }: { conversation: Conversation; onSaved: () => Promise<void> }) {
  const [items, setItems] = useState<Memory[]>([])
  const [enabled, setEnabled] = useState(false)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    let active = true
    void Promise.all([memoryApi.settings(), memoryApi.suggestions(conversation.id)]).then(([s, list]) => { if (active) { setEnabled(s.memory_enabled); setItems(list.items) } }).catch(() => {})
    return () => { active = false }
  }, [conversation.id, conversation.brief_revision])
  if (conversation.temporary) return <p className="memory-suggestions">گفت‌وگوی بدون حافظه: ترجیح ذخیره‌شده خوانده یا نوشته نمی‌شود.</p>
  if (!enabled) return null
  return <section className="memory-suggestions" aria-label="ترجیح‌های ذخیره‌شده برای این خرید"><h2>از شناخت من برای این خرید</h2>
    <p>دستور صریح این گفت‌وگو مقدم است؛ هیچ مقایسه‌ای خودکار تغییر نمی‌کند.</p>
    {!conversation.brief.confirmed && items.map(item => <div key={item.id}><span>{preferenceLabel(item)}</span> <button className="text-button" disabled={busy} onClick={async () => {
      setBusy(true); try { await memoryApi.apply(conversation.id, conversation.brief_revision, item); await onSaved(); setMessage('ترجیح بررسی شد؛ معیار صریح موجود تغییر نمی‌کند. نیاز را بازبینی و تأیید کنید.') } catch (reason) { setMessage(failureText(reason)) } finally { setBusy(false) }
    }}>استفاده در این خرید</button></div>)}
    {conversation.brief.confirmed && <button className="button ghost" disabled={busy} onClick={async () => {
      setBusy(true); try { const r = await memoryApi.propose(conversation.id, conversation.brief_revision); setMessage(r.items.length ? 'پیشنهادها در شناخت من منتظر بررسی شما هستند.' : 'معیار ساختاریافتهٔ مرتبطی برای پیشنهاد وجود ندارد.') } catch (reason) { setMessage(failureText(reason)) } finally { setBusy(false) }
    }}>پیشنهاد ترجیح برای شناخت من</button>}
    {message && <p role="status">{message}</p>}
  </section>
}
