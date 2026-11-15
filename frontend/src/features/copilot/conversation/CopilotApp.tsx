import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

import { copilotApi, CopilotApiError, newIdempotencyKey } from './api'
import { Icon } from './Icons'
import type { Conversation, ConversationSummary, OperationStatus, Upload } from './types'

type MobilePane = 'conversation' | 'desk'

const errorText = (error: unknown) => error instanceof CopilotApiError ? error.message : 'ارتباط برقرار نشد؛ دوباره تلاش کنید.'

function BriefEditor({ conversation, onSaved }: { conversation: Conversation; onSaved: () => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [recipient, setRecipient] = useState(conversation.brief.recipient_context ?? '')
  const [category, setCategory] = useState(conversation.brief.category ?? '')
  const [budget, setBudget] = useState(conversation.brief.budget_toman?.toString() ?? '')
  const [useCases, setUseCases] = useState(conversation.brief.use_cases.join('، '))
  const [busy, setBusy] = useState(false)

  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true)
    try {
      await copilotApi.editBrief(conversation.id, conversation.brief_revision, {
        recipient_context: recipient || null,
        category: category.trim() || null,
        budget_toman: budget.trim() === '' ? null : budget,
        use_cases: useCases.split('،').map((item) => item.trim()).filter(Boolean),
      })
      await onSaved(); setOpen(false)
    } finally { setBusy(false) }
  }

  return <section className="brief-ribbon" aria-labelledby="brief-title">
    <div><p className="overline">brief نسخهٔ {conversation.brief_revision.toLocaleString('fa-IR')}</p><h2 id="brief-title">آنچه فعلاً قطعی است</h2></div>
    <div className="brief-chips">
      <span>{conversation.brief.recipient_context === 'GIFT' ? 'برای هدیه' : conversation.brief.recipient_context === 'HOUSEHOLD' ? 'برای خانه' : conversation.brief.recipient_context === 'SELF' ? 'برای خودم' : 'مخاطب نامعلوم'}</span>
      <span>{conversation.brief.category ?? 'دسته نامعلوم'}</span>
      <span>{conversation.brief.budget_toman === null ? 'بودجه نامعلوم' : `${conversation.brief.budget_toman.toLocaleString('fa-IR')} تومان`}</span>
    </div>
    <button className="text-button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>ویرایش brief</button>
    {open && <form className="brief-form" onSubmit={save}>
      <label>مخاطب<select value={recipient} onChange={(e) => setRecipient(e.target.value)}><option value="">نامعلوم</option><option value="SELF">خودم</option><option value="GIFT">هدیه</option><option value="HOUSEHOLD">خانه</option></select></label>
      <label>دسته<input value={category} onChange={(e) => setCategory(e.target.value)} maxLength={120} /></label>
      <label>سقف بودجه (تومان)<input inputMode="numeric" value={budget} onChange={(e) => setBudget(e.target.value)} /></label>
      <label>کاربردها، جدا با «،»<input value={useCases} onChange={(e) => setUseCases(e.target.value)} /></label>
      <div className="inline-actions"><button className="button primary" disabled={busy}>ذخیره</button><button type="button" className="button ghost" onClick={() => setOpen(false)}>بستن</button></div>
    </form>}
  </section>
}

export function CopilotApp() {
  const [items, setItems] = useState<ConversationSummary[]>([])
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [text, setText] = useState('')
  const [draftReply, setDraftReply] = useState('')
  const [operationId, setOperationId] = useState<string | null>(null)
  const [operationStatus, setOperationStatus] = useState<OperationStatus | null>(null)
  const [lastSubmittedText, setLastSubmittedText] = useState('')
  const [uploads, setUploads] = useState<Upload[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [pane, setPane] = useState<MobilePane>('conversation')
  const sourceRef = useRef<EventSource | null>(null)
  const seenRef = useRef(new Set<string>())
  const reconcileTimerRef = useRef<number | null>(null)

  const refreshList = async () => setItems((await copilotApi.list()).items)
  const open = async (id: string) => { setConversation(await copilotApi.get(id)); setUploads([]); setDraftReply(''); setError(null) }
  const refresh = async () => { if (conversation) setConversation(await copilotApi.get(conversation.id)); await refreshList() }

  useEffect(() => {
    void (async () => {
      try { await copilotApi.bootstrap(); const list = await copilotApi.list(); setItems(list.items); if (list.items[0]) await open(list.items[0].id) }
      catch (reason) { setError(errorText(reason)) }
      finally { setLoading(false) }
    })()
    return () => {
      sourceRef.current?.close()
      sourceRef.current = null
      if (reconcileTimerRef.current !== null) window.clearTimeout(reconcileTimerRef.current)
    }
  }, [])

  const create = async () => { if (loading) return; const item = await copilotApi.create(); await refreshList(); await open(item.id) }
  const follow = (url: string, followedOperationId: string) => {
    sourceRef.current?.close(); seenRef.current.clear(); setDraftReply('')
    if (reconcileTimerRef.current !== null) window.clearTimeout(reconcileTimerRef.current)
    const source = new EventSource(url); sourceRef.current = source
    source.addEventListener('operation.started', () => setOperationStatus('RUNNING'))
    source.addEventListener('assistant.text.delta', (rawEvent) => {
      const event = rawEvent as MessageEvent<string>
      if (seenRef.current.has(event.lastEventId)) return
      seenRef.current.add(event.lastEventId)
      const payload = JSON.parse(event.data) as { text: string }
      setDraftReply((value) => value + payload.text)
    })
    const finish = (status: OperationStatus) => {
      setOperationStatus(status)
      setDraftReply('')
      source.close()
      if (sourceRef.current === source) sourceRef.current = null
      void refresh()
    }
    const reconcile = async (pollUntilTerminal: boolean) => {
      try {
        const current = await copilotApi.operation(followedOperationId)
        if (['COMPLETED', 'FAILED', 'CANCELLED', 'INTERRUPTED'].includes(current.status)) {
          finish(current.status)
          return
        }
        setOperationStatus(current.status)
        setError('stream قطع شد؛ وضعیت authoritative بازیابی شد و اتصال دوباره برقرار می‌شود.')
        if (pollUntilTerminal && sourceRef.current === source) {
          reconcileTimerRef.current = window.setTimeout(() => void reconcile(true), 500)
        }
      } catch (reason) {
        setError(errorText(reason))
      }
    }
    source.addEventListener('operation.completed', () => finish('COMPLETED'))
    source.addEventListener('operation.cancelled', () => finish('CANCELLED'))
    source.addEventListener('operation.failed', (rawEvent) => {
      const event = rawEvent as MessageEvent<string>
      finish((JSON.parse(event.data) as { code?: string }).code === 'WORKER_INTERRUPTED' ? 'INTERRUPTED' : 'FAILED')
    })
    source.addEventListener('stream.replay_gap', () => {
      source.close()
      setDraftReply('')
      void reconcile(true)
    })
    source.onerror = () => { void reconcile(false) }
  }
  const submitMessage = async (messageText: string, uploadIds: string[]) => {
    if (!conversation || !messageText || operationStatus === 'RUNNING') return
    setError(null)
    try {
      const accepted = await copilotApi.send(conversation.id, messageText, conversation.brief_revision, uploadIds, newIdempotencyKey())
      setLastSubmittedText(messageText)
      setText(''); setUploads([]); setOperationId(accepted.operation.id); setOperationStatus(accepted.operation.status); follow(accepted.events_url, accepted.operation.id); await refresh()
    } catch (reason) { setError(errorText(reason)) }
  }
  const send = async (event: FormEvent) => {
    event.preventDefault()
    await submitMessage(text.trim(), uploads.map((item) => item.id))
  }
  const retry = async () => {
    if (!lastSubmittedText) return
    await submitMessage(lastSubmittedText, [])
  }
  const stop = async () => { if (operationId) { await copilotApi.cancel(operationId); setOperationStatus('CANCELLED') } }
  const attach = async (file?: File) => {
    if (!conversation || !file) return
    if (file.size > 5 * 1024 * 1024) { setError('حجم تصویر باید حداکثر ۵ مگابایت باشد.'); return }
    try {
      const uploaded = await copilotApi.upload(conversation.id, file)
      setUploads((current) => [...current, uploaded])
    }
    catch (reason) { setError(errorText(reason)) }
  }

  return <div className="copilot-shell" dir="rtl">
    <a className="skip-link" href="#copilot-main">رفتن به محتوای اصلی</a>
    <nav className="copilot-nav" aria-label="ناوبری دستیار خرید"><a className="copilot-logo" href="/" aria-label="قبل از خرید"><span>ب</span></a><button aria-label="گفت‌وگوی تازه" disabled={loading} onClick={() => void create()}><Icon name="plus" /></button><a href="/" aria-label="تحلیل قبلی"><Icon name="desk" /></a></nav>
    <aside className={`conversation-pane ${pane === 'conversation' ? 'mobile-active' : ''}`} aria-label="گفت‌وگو">
      <header className="copilot-heading"><div><p className="overline">حالت توسعه / fixture</p><h1>همراه خرید</h1></div><span className="fixture-badge">بدون AI زنده</span></header>
      <div className="conversation-history" aria-label="تاریخچه گفت‌وگوها">
        <button className="new-conversation" disabled={loading} onClick={() => void create()}><Icon name="plus" /> گفت‌وگوی تازه</button>
        {items.map((item) => <button key={item.id} className={conversation?.id === item.id ? 'active' : ''} onClick={() => void open(item.id)}>{item.title}</button>)}
      </div>
      <div className="thread" aria-live="off">
        {loading && <p className="muted">در حال آماده‌سازی…</p>}
        {!loading && !conversation && <div className="thread-empty"><Icon name="chat" /><p>برای روشن‌کردن نیاز خرید، یک گفت‌وگو بسازید.</p></div>}
        {conversation?.messages.map((message) => <article key={message.id} className={`message ${message.role.toLowerCase()}`}><span>{message.role === 'USER' ? 'شما' : 'همراه خرید'}</span><p>{message.text}</p></article>)}
        {draftReply && <article className="message assistant provisional"><span>fixture در حال نوشتن</span><p>{draftReply}</p></article>}
      </div>
      {error && <div className="copilot-error" role="alert">{error}</div>}
      {lastSubmittedText && ['FAILED', 'CANCELLED', 'INTERRUPTED'].includes(operationStatus ?? '') && <div className="retry-row"><span>این اجرا کامل نشد.</span><button type="button" className="text-button" onClick={() => void retry()}>تلاش دوباره</button></div>}
      <p className="sr-status" role="status" aria-live="polite">{operationStatus === 'RUNNING' ? 'پاسخ fixture در حال تولید است.' : operationStatus === 'COMPLETED' ? 'پاسخ کامل شد.' : ''}</p>
      <form className="composer" onSubmit={send}>
        {uploads.length > 0 && <div className="upload-strip">{uploads.map((item) => <span key={item.id}>تصویر {item.width.toLocaleString('fa-IR')}×{item.height.toLocaleString('fa-IR')}</span>)}</div>}
        <textarea aria-label="پیام شما" placeholder="دربارهٔ خریدتان بنویسید…" value={text} onChange={(e) => setText(e.target.value)} maxLength={8000} disabled={!conversation} />
        <div className="composer-actions"><label className="icon-button" aria-label="افزودن تصویر"><Icon name="image" /><input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => void attach(e.target.files?.[0])} disabled={!conversation || uploads.length >= 3} /></label>{operationStatus === 'RUNNING' ? <button type="button" className="icon-button stop" onClick={() => void stop()} aria-label="توقف تولید"><Icon name="stop" /></button> : <button className="send-button" disabled={!conversation || !text.trim()} aria-label="ارسال پیام"><Icon name="send" /></button>}</div>
      </form>
    </aside>
    <main id="copilot-main" className={`choice-desk ${pane === 'desk' ? 'mobile-active' : ''}`} tabIndex={-1}>
      {conversation && <BriefEditor conversation={conversation} onSaved={refresh} />}
      <section className="desk-empty" aria-labelledby="desk-title"><div className="desk-orbit" aria-hidden="true"><Icon name="desk" /></div><p className="overline">Choice Desk · آماده‌سازی</p><h2 id="desk-title">هنوز گزینه‌ای برای مقایسه نداریم.</h2><p>در این milestone فقط brief و مسیر گفت‌وگو آماده می‌شود. پژوهش منبع، قیمت بازار، رتبه‌بندی و پیشنهاد محصول هنوز اجرا نشده‌اند و چیزی به‌صورت ساختگی نمایش داده نمی‌شود.</p><ol><li>brief را با اطلاعات قطعی تکمیل کنید.</li><li>در milestone بعد، پژوهش محدود و منبع‌دار با اقدام صریح شما آغاز می‌شود.</li><li>سپس گزینه‌ها در این میز مقایسه خواهند شد.</li></ol></section>
    </main>
    <nav className="mobile-switcher" aria-label="نمای موبایل"><button className={pane === 'conversation' ? 'active' : ''} onClick={() => setPane('conversation')}><Icon name="chat" />گفت‌وگو</button><button className={pane === 'desk' ? 'active' : ''} onClick={() => setPane('desk')}><Icon name="desk" />میز انتخاب</button></nav>
  </div>
}
