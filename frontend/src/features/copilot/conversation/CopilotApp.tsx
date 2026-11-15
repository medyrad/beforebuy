import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

import { copilotApi, CopilotApiError, newIdempotencyKey } from './api'
import { Icon } from './Icons'
import type { Answer, Conversation, ConversationSummary, OperationStatus, ResearchJob, Upload } from './types'
import { HistoryDrawer } from './HistoryDrawer'
import { memoryApi } from '../memory/api'
import type { Settings } from '../memory/api'
import { ChoiceDesk } from '../choice-desk/ChoiceDesk'
import { ComparisonProfile } from '../choice-desk/ComparisonProfile'
import { AssistantSettings } from '../memory/AssistantSettings'
import { MemoryPanel } from '../memory/MemoryPanel'
import { MemorySuggestions } from '../memory/MemorySuggestions'
import '../memory/memory.css'
import './workspace.css'

type MobilePane = 'conversation' | 'desk'

const errorText = (error: unknown) => error instanceof CopilotApiError
  ? error.message.replaceAll('brief', 'نیاز خرید').replaceAll('fixture', 'نسخهٔ نمایشی').replaceAll('revision', 'نسخه').replaceAll('idempotency', 'درخواست')
  : 'ارتباط برقرار نشد؛ دوباره تلاش کنید.'

function BriefEditor({ conversation, onSaved }: { conversation: Conversation; onSaved: () => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [recipient, setRecipient] = useState(conversation.brief.recipient_context ?? '')
  const [category, setCategory] = useState(conversation.brief.category ?? '')
  const [budget, setBudget] = useState(conversation.brief.budget_toman?.toString() ?? '')
  const [useCases, setUseCases] = useState(conversation.brief.use_cases.join('، '))
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState(conversation.brief.comparison ?? {})
  const [failure, setFailure] = useState('')
  const confirm = async () => {
    setBusy(true)
    try { await copilotApi.confirmBrief(conversation.id, conversation.brief_revision); await onSaved() }
    catch (reason) { setFailure(errorText(reason)) }
    finally { setBusy(false) }
  }

  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true)
    try {
      await copilotApi.editBrief(conversation.id, conversation.brief_revision, {
        recipient_context: recipient || null,
        category: category.trim() || null,
        budget_toman: budget.trim() === '' ? null : budget,
        use_cases: useCases.split('،').map((item) => item.trim()).filter(Boolean),
        comparison: profile,
      })
      await onSaved(); setOpen(false)
    } catch (reason) { setFailure(errorText(reason)) } finally { setBusy(false) }
  }

  return <section className="brief-ribbon" aria-labelledby="brief-title">
    <div><p className="overline">{conversation.brief.confirmed ? 'تأییدشده توسط شما' : 'برداشت از گفته‌های شما؛ هنوز تأیید نشده'}</p><h2 id="brief-title">نیاز خرید شما</h2></div>
    <div className="brief-chips">
      <span>{conversation.brief.recipient_context === 'GIFT' ? 'برای هدیه' : conversation.brief.recipient_context === 'HOUSEHOLD' ? 'برای خانه' : conversation.brief.recipient_context === 'SELF' ? 'برای خودم' : 'مخاطب نامعلوم'}</span>
      <span>{{ electronics: 'دیجیتال', home: 'خانه', sports: 'پوشاک و ورزش', other: 'سایر خریدها' }[conversation.brief.category ?? ''] ?? conversation.brief.category ?? 'دسته نامعلوم'}</span>
      <span>{conversation.brief.budget_toman === null ? 'بودجه نامعلوم' : `${conversation.brief.budget_toman.toLocaleString('fa-IR')} تومان`}</span>
    </div>
    {conversation.brief.conversation_state?.pending_budget && <p>تغییر بودجه در انتظار پاسخ شما در گفت‌وگو است.</p>}
    <div className="brief-actions"><button className="text-button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>اصلاح نیاز خرید</button>{!conversation.brief.confirmed && !conversation.brief.conversation_state?.pending_budget && <button className="text-button confirm" disabled={busy} onClick={() => void confirm()}>تأیید نیاز خرید</button>}</div>
    {open && <form className="brief-form" onSubmit={save}>
      <label>مخاطب<select value={recipient} onChange={(e) => setRecipient(e.target.value)}><option value="">نامعلوم</option><option value="SELF">خودم</option><option value="GIFT">هدیه</option><option value="HOUSEHOLD">خانه</option></select></label>
      <label>دسته<input value={category} onChange={(e) => setCategory(e.target.value)} maxLength={120} /></label>
      <label>سقف بودجه (تومان)<input inputMode="numeric" value={budget} onChange={(e) => setBudget(e.target.value)} /></label>
      <label>کاربردها، جدا با «،»<input value={useCases} onChange={(e) => setUseCases(e.target.value)} /></label>
      <ComparisonProfile value={profile} onChange={setProfile} category={category} recipient={recipient} />
      <div className="inline-actions"><button className="button primary" disabled={busy}>ذخیره</button><button type="button" className="button ghost" onClick={() => setOpen(false)}>بستن</button></div>
    </form>}
    {failure && <p role="alert">{failure}</p>}
  </section>
}

export function CopilotApp() {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [sending, setSending] = useState(false)
  const sendingRef = useRef(false)
  const selectedRef = useRef<string | null>(null)
  const epochRef = useRef(0)
  const refreshSequence = useRef(0)
  const draftsRef = useRef<Record<string, { text: string; urls: string; uploads: Upload[]; job: ResearchJob | null; scroll: number }>>({})
  const threadRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const nearBottom = useRef(true)
  const [newMessages, setNewMessages] = useState(false)
  const [view, setView] = useState<'desk' | 'settings' | 'memory'>('desk')
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
  const [researchUrls, setResearchUrls] = useState('')
  const [researchJob, setResearchJob] = useState<ResearchJob | null>(null)
  const [researchBusy, setResearchBusy] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)
  const seenRef = useRef(new Set<string>())
  const reconcileTimerRef = useRef<number | null>(null)
  const researchTimerRef = useRef<number | null>(null)

  const refreshList = async () => setItems((await copilotApi.list()).items)
  const detach = () => {
    epochRef.current += 1
    sourceRef.current?.close(); sourceRef.current = null
    if (reconcileTimerRef.current !== null) window.clearTimeout(reconcileTimerRef.current)
    if (researchTimerRef.current !== null) window.clearTimeout(researchTimerRef.current)
  }
  const saveDraft = () => { draftsRef.current[selectedRef.current ?? 'home'] = { text, urls: researchUrls, uploads, job: researchJob, scroll: threadRef.current?.scrollTop ?? 0 } }
  const open = async (id: string) => {
    saveDraft(); detach(); const epoch = epochRef.current; selectedRef.current = id
    setDraftReply(''); setOperationId(null); setOperationStatus(null); setLastSubmittedText(''); setError(null); setLoading(true)
    try {
      const next = await copilotApi.get(id)
      if (epoch !== epochRef.current) return
      setConversation(next); setPane('conversation'); setView('desk')
      const saved = draftsRef.current[id]
      setText(saved?.text ?? ''); setUploads(saved?.uploads ?? []); setResearchUrls(saved?.urls ?? ''); setResearchJob(saved?.job ?? null); setResearchBusy(false)
      nearBottom.current = !saved; setNewMessages(false)
      requestAnimationFrame(() => { if (threadRef.current && epoch === epochRef.current) threadRef.current.scrollTop = saved?.scroll ?? threadRef.current.scrollHeight })
      const running = next.operations.find((o) => o.operation_kind !== 'RESEARCH' && ['PENDING', 'RUNNING'].includes(o.status))
      if (running) { setOperationId(running.id); setOperationStatus(running.status); follow(`/api/v1/operations/${running.id}/events`, running.id) }
      if (saved?.job && ['PENDING', 'RUNNING'].includes(saved.job.status)) { setResearchBusy(true); void pollResearch(saved.job.id) }
    } catch (reason) { if (epoch === epochRef.current) { setConversation(null); setError('گفت‌وگو در دسترس نیست یا منقضی شده است.'); throw reason } }
    finally { if (epoch === epochRef.current) setLoading(false) }
  }
  const fresh = () => {
    setView('desk')
    saveDraft(); detach(); selectedRef.current = null; setConversation(null); setText(''); setUploads([])
    setResearchUrls(''); setResearchJob(null); setResearchBusy(false); setDraftReply(''); setOperationId(null); setOperationStatus(null)
    setLastSubmittedText(''); setError(null); setPane('conversation'); nearBottom.current = true; setNewMessages(false)
  }
  const refresh = async () => {
    const id = selectedRef.current; const epoch = epochRef.current
    const sequence = ++refreshSequence.current
    if (id) { const next = await copilotApi.get(id); if (epoch === epochRef.current && sequence === refreshSequence.current) { setConversation(next); if (!nearBottom.current) setNewMessages(true) } }
    await refreshList()
  }

  useEffect(() => {
    void (async () => {
      try { await copilotApi.bootstrap(); const list = await copilotApi.list(); setItems(list.items); setSettings(await memoryApi.settings()) }
      catch (reason) { setError(errorText(reason)) }
      finally { setLoading(false) }
    })()
    return () => {
      sourceRef.current?.close()
      epochRef.current += 1
      sourceRef.current = null
      if (reconcileTimerRef.current !== null) window.clearTimeout(reconcileTimerRef.current)
      if (researchTimerRef.current !== null) window.clearTimeout(researchTimerRef.current)
    }
  }, [])

  useEffect(() => {
    const thread = threadRef.current
    if (!thread) return
    if (nearBottom.current) thread.scrollTop = thread.scrollHeight
  }, [draftReply, conversation?.messages.length])
  useEffect(() => {
    const area = inputRef.current
    if (area) { area.style.height = 'auto'; area.style.height = `${Math.min(area.scrollHeight, 112)}px` }
  }, [text])

  const create = async (temporary = false) => { if (loading) return; try { const item = await copilotApi.create(temporary); await refreshList(); await open(item.id) } catch (reason) { setError(errorText(reason)) } }
  const follow = (url: string, followedOperationId: string) => {
    const epoch = epochRef.current
    const current = () => epoch === epochRef.current
    sourceRef.current?.close(); seenRef.current.clear(); setDraftReply('')
    if (reconcileTimerRef.current !== null) window.clearTimeout(reconcileTimerRef.current)
    const source = new EventSource(url); sourceRef.current = source
    source.addEventListener('operation.started', () => { if (current()) setOperationStatus('RUNNING') })
    source.addEventListener('assistant.text.delta', (rawEvent) => {
      const event = rawEvent as MessageEvent<string>
      if (!current()) return
      if (seenRef.current.has(event.lastEventId)) return
      seenRef.current.add(event.lastEventId)
      const payload = JSON.parse(event.data) as { text: string }
      setDraftReply((value) => value + payload.text)
      if (!nearBottom.current) setNewMessages(true)
    })
    const finish = (status: OperationStatus) => {
      if (!current()) return
      setOperationStatus(status)
      setDraftReply('')
      source.close()
      if (sourceRef.current === source) sourceRef.current = null
      void refresh().catch(() => { if (current()) setError('دریافت پاسخ نهایی انجام نشد؛ گفت‌وگو را دوباره باز کنید.') })
    }
    const reconcile = async (pollUntilTerminal: boolean) => {
      try {
        const operation = await copilotApi.operation(followedOperationId)
        if (!current()) return
        if (['COMPLETED', 'FAILED', 'CANCELLED', 'INTERRUPTED'].includes(operation.status)) {
          finish(operation.status)
          return
        }
        setOperationStatus(operation.status)
        setError('ارتباط پاسخ قطع شد؛ در حال بازیابی وضعیت هستیم.')
        if (pollUntilTerminal && sourceRef.current === source) {
          reconcileTimerRef.current = window.setTimeout(() => void reconcile(true), 500)
        }
      } catch (reason) {
        if (current()) setError(errorText(reason))
      }
    }
    source.addEventListener('operation.completed', () => finish('COMPLETED'))
    source.addEventListener('operation.cancelled', () => finish('CANCELLED'))
    source.addEventListener('operation.failed', (rawEvent) => {
      const event = rawEvent as MessageEvent<string>
      finish((JSON.parse(event.data) as { code?: string }).code === 'WORKER_INTERRUPTED' ? 'INTERRUPTED' : 'FAILED')
    })
    source.addEventListener('stream.replay_gap', () => {
      if (!current()) return
      source.close()
      setDraftReply('')
      void reconcile(true)
    })
    source.onerror = () => { void reconcile(false) }
  }
  const submitMessage = async (messageText: string, uploadIds: string[], answer?: Answer) => {
    if (!messageText || sendingRef.current || ['PENDING', 'RUNNING'].includes(operationStatus ?? '')) return
    sendingRef.current = true; setSending(true)
    const epoch = epochRef.current
    setError(null)
    try {
      const target = conversation ?? await copilotApi.create()
      if (epoch !== epochRef.current) return
      selectedRef.current = target.id; setConversation(target)
      const accepted = await copilotApi.send(target.id, messageText, target.brief_revision, uploadIds, newIdempotencyKey(), answer)
      if (epoch !== epochRef.current) return
      nearBottom.current = true
      setLastSubmittedText(messageText)
      setText(''); setUploads([]); setOperationId(accepted.operation.id); setOperationStatus(accepted.operation.status); follow(accepted.events_url, accepted.operation.id); await refresh()
    } catch (reason) { if (epoch === epochRef.current) setError(errorText(reason)) }
    finally { sendingRef.current = false; setSending(false) }
  }
  const send = async (event: FormEvent) => {
    event.preventDefault()
    await submitMessage(text.trim(), uploads.map((item) => item.id))
  }
  const retry = async () => {
    if (!lastSubmittedText) return
    await submitMessage(lastSubmittedText, [])
  }
  const stop = async () => {
    const epoch = epochRef.current
    if (!operationId) return
    try {
      const stopped = await copilotApi.cancel(operationId).catch((reason: unknown) => {
        if (reason instanceof CopilotApiError && reason.code === 'OPERATION_TERMINAL') return copilotApi.operation(operationId)
        throw reason
      })
      if (epoch === epochRef.current) { setOperationStatus(stopped.status); setDraftReply(''); await refresh() }
    } catch (reason) { if (epoch === epochRef.current) setError(errorText(reason)) }
  }
  const attach = async (file?: File) => {
    if (!file) return
    const epoch = epochRef.current
    if (file.size > 5 * 1024 * 1024) { setError('حجم تصویر باید حداکثر ۵ مگابایت باشد.'); return }
    try {
      const target = conversation ?? await copilotApi.create()
      if (epoch !== epochRef.current) return
      selectedRef.current = target.id; setConversation(target)
      const uploaded = await copilotApi.upload(target.id, file)
      if (epoch === epochRef.current) setUploads((current) => [...current, uploaded])
    }
    catch (reason) { if (epoch === epochRef.current) setError(errorText(reason)) }
  }

  const pollResearch = async (jobId: string) => {
    const epoch = epochRef.current
    try {
      const next = await copilotApi.research(jobId)
      if (epoch !== epochRef.current) return
      setResearchJob(next)
      if (['PENDING', 'RUNNING'].includes(next.status)) researchTimerRef.current = window.setTimeout(() => void pollResearch(jobId), 750)
      else setResearchBusy(false)
    } catch (reason) { if (epoch === epochRef.current) { setResearchBusy(false); setError(errorText(reason)) } }
  }

  const startResearch = async (event: FormEvent) => {
    event.preventDefault()
    if (!conversation) return
    const epoch = epochRef.current
    const urls = researchUrls.split(/\r?\n/).map((item) => item.trim()).filter(Boolean)
    if (urls.length < 1 || urls.length > 3) { setError('بین یک تا سه لینک دقیق محصول وارد کنید.'); return }
    try {
      const targets = urls.map((url) => {
        const parsed = new URL(url)
        if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.search || parsed.hash) throw new Error('invalid')
        return { source_id: parsed.hostname.toLowerCase(), url: parsed.toString() }
      })
      setError(null); setResearchBusy(true)
      const accepted = await copilotApi.startResearch(conversation.id, conversation.brief_revision, targets, newIdempotencyKey())
      if (epoch !== epochRef.current) return
      setResearchJob(accepted.job)
      if (['PENDING', 'RUNNING'].includes(accepted.job.status)) await pollResearch(accepted.job.id)
      else setResearchBusy(false)
    } catch (reason) {
      if (epoch !== epochRef.current) return
      setResearchBusy(false)
      setError(reason instanceof Error && reason.message === 'invalid' ? 'لینک کامل و امن صفحهٔ محصول را بدون بخش جست‌وجو یا نشانهٔ انتهایی وارد کنید.' : errorText(reason))
    }
  }

  const active = sending || ['PENDING', 'RUNNING'].includes(operationStatus ?? '')
  const hasNeed = conversation && (conversation.brief.budget_toman !== null || conversation.brief.category)
  const setPrompt = (value: string) => { setText(value); inputRef.current?.focus() }
  return <div className="shopping-app" dir="rtl"><nav className="copilot-utility" aria-label="تنظیمات و شناخت شخصی">
    <button className="wordmark" onClick={() => { fresh(); setView('desk') }}>قبل از خرید<span>همراه تصمیم‌های شما</span></button>
    <button aria-pressed={view === 'desk'} onClick={() => { setView('desk'); void memoryApi.settings().then(setSettings).catch(() => setSettings(null)) }}>میز خرید</button>
    <button onClick={() => setHistoryOpen(true)}>گفت‌وگوهای من</button>
    <button aria-pressed={view === 'settings'} onClick={() => setView('settings')}>تنظیمات دستیار</button>
    <button aria-pressed={view === 'memory'} onClick={() => setView('memory')}>شناخت من</button>
    <a href="/legacy">نسخهٔ قبلی</a>
  </nav>
  {historyOpen && <HistoryDrawer close={() => setHistoryOpen(false)} open={open} fresh={fresh} deleted={(id) => {
    if (!id || id === selectedRef.current) fresh()
    if (id) delete draftsRef.current[id]; else draftsRef.current = {}
    void refreshList()
  }} />}
  {view !== 'desk' && <main className="personal-page">{view === 'settings' ? <AssistantSettings /> : <MemoryPanel />}</main>}
  <div className="copilot-shell" dir="rtl" style={view !== 'desk' ? { display: 'none' } : undefined}>
    <a className="skip-link" href="#copilot-main">رفتن به محتوای اصلی</a>
    <aside className={`conversation-pane ${pane === 'conversation' ? 'mobile-active' : ''}`} aria-label="گفت‌وگو">
      <header className="copilot-heading"><div><p className="overline">یک خرید، یک تصمیم روشن‌تر</p><h1>{conversation ? 'همراه خرید' : 'برای چه خریدی کمکت کنم؟'}</h1></div><button className="text-button" disabled={loading || sending} onClick={fresh}><Icon name="plus" />خرید تازه</button></header>
      <div className="provider-strip"><span>{!settings ? 'وضعیت اتصال در دسترس نیست' : settings.mode === 'DEMONSTRATION' ? 'نسخهٔ نمایشی' : settings.mode === 'LIVE_READY' ? 'آمادهٔ اتصال زنده' : 'اتصال زنده غیرفعال'}</span>
        {settings && <details><summary>وضعیت دستیار</summary><p>ارائه‌دهندهٔ منتخب: <bdi>{settings.provider}</bdi> · مدل: <bdi>{settings.model}</bdi></p><p>{settings.credential_state === 'VALIDATED' ? 'کلید منتخب اعتبارسنجی شده است؛ حالت اجرا مستقل است.' : settings.credential_state === 'STORED_UNVALIDATED' ? 'کلید منتخب ذخیره شده، اما اعتبارسنجی نشده است.' : 'اتصال منتخب تأیید نشده؛ جزئیات در تنظیمات دستیار است.'} {settings.connection === 'VALIDATION_BLOCKED' ? ' اعتبارسنجی این ارائه‌دهنده برای منطقهٔ فعلی مسدود است.' : ''} ذخیرهٔ کلید، مجوز هزینه یا فعال‌سازی نیست.</p></details>}
      </div>
      <div className="thread" ref={threadRef} tabIndex={0} aria-label="پیام‌های گفت‌وگو" aria-live="off" onScroll={() => { const el = threadRef.current; if (el) { nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 64; if (nearBottom.current) setNewMessages(false) } }}>
        {loading && <p className="muted">در حال آماده‌سازی…</p>}
        {!loading && !conversation && <section className="welcome"><p>نیازت را بگو؛ با هم ابهام‌ها را روشن می‌کنیم، بعد سراغ گزینه‌های قابل‌بررسی می‌رویم.</p>
          <div className="category-grid">{[
            ['digital', 'دیجیتال', 'برای خرید یک وسیلهٔ دیجیتال کمک می‌خواهم.'], ['appliance', 'لوازم خانگی', 'برای خانه یک وسیلهٔ کاربردی می‌خواهم.'],
            ['living', 'خانه و زندگی', 'برای انتخاب صندلی راحتی کمک می‌خواهم.'], ['sport', 'پوشاک و ورزش', 'برای پیاده‌روی کفش می‌خواهم.'],
            ['gift', 'هدیه', 'می‌خواهم برای یک دوست هدیه بخرم.'], ['other', 'سایر خریدها', 'برای یک خرید دیگر کمک می‌خواهم.'],
          ].map(([icon, label, prompt]) => <button key={icon} onClick={() => setPrompt(prompt)}><CategoryIcon kind={icon} /><span>{label}</span></button>)}</div>
          <p className="welcome-note">از هر خریدی می‌توانیم صحبت کنیم؛ مقایسه و قیمت فقط با شواهد کافی نمایش داده می‌شود.</p>
          <div className="example-prompts"><span>مثلاً…</span>{['گوشی‌ام شکسته؛ خرید بعدی را چطور انتخاب کنم؟', 'برای آشپزخانهٔ کوچک چه چیزهایی مهم است؟', 'برای دوستی که اهل سفر است هدیه می‌خواهم.'].map((prompt) => <button key={prompt} onClick={() => setPrompt(prompt)}>{prompt}</button>)}</div>
          {items[0] && <button className="continue-chat" onClick={() => void open(items[0].id).catch(() => {})}>ادامهٔ گفت‌وگو: <bdi>{items[0].title}</bdi></button>}
          <button className="text-button" onClick={() => void create(true)}>گفت‌وگوی بدون حافظه</button>
        </section>}
        {conversation?.messages_truncated && <p>۲۰۰ پیام آخر نمایش داده می‌شود.</p>}
        {conversation?.messages.map((message, index) => <article key={message.id} className={`message ${message.role.toLowerCase()}`}><span>{message.role === 'USER' ? 'شما' : 'همراه خرید'}</span><p dir="auto">{message.text}</p>
          {!!message.reply_actions?.length && <div className="reply-options" aria-label="پاسخ‌های پیشنهادی">{message.reply_actions.map((action) => <button key={action.id} disabled={active || index !== conversation.messages.length - 1 || action.revision !== conversation.brief_revision} onClick={() => void submitMessage(action.label, [], { question_id: action.question_id, action_id: action.id, revision: action.revision })}>{action.label}</button>)}</div>}
        </article>)}
        {draftReply && <article className="message assistant provisional"><span>در حال آماده‌کردن پاسخ؛ هنوز نهایی نیست</span><p dir="auto">{draftReply}</p></article>}
      </div>
      {newMessages && <button className="jump-latest" onClick={() => { nearBottom.current = true; setNewMessages(false); if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight }}>پیام‌های جدید ↓</button>}
      {error && <div className="copilot-error" role="alert">{error}</div>}
      {lastSubmittedText && ['FAILED', 'CANCELLED', 'INTERRUPTED'].includes(operationStatus ?? '') && <div className="retry-row"><span>این اجرا کامل نشد.</span><button type="button" className="text-button" onClick={() => void retry()}>تلاش دوباره</button></div>}
      <p className="sr-status" role="status" aria-live="polite">{active ? 'پاسخ در حال آماده‌شدن است.' : operationStatus === 'COMPLETED' ? 'پاسخ کامل شد.' : ''}</p>
      <form className="composer" onSubmit={send}>
        {uploads.length > 0 && <div className="upload-strip">{uploads.map((item) => <span key={item.id}>تصویر {item.width.toLocaleString('fa-IR')}×{item.height.toLocaleString('fa-IR')}</span>)}</div>}
        <textarea ref={inputRef} rows={2} aria-label="پیام شما" placeholder="دربارهٔ خریدتان بنویسید…" value={text} onChange={(e) => setText(e.target.value)} maxLength={8000} disabled={loading} />
        <div className="composer-actions"><label className="icon-button upload-control"><Icon name="image" /><input aria-label="افزودن تصویر" type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => void attach(e.target.files?.[0])} disabled={loading || active || uploads.length >= 3} /></label><small>پاسخ دلخواهتان را هم می‌توانید بنویسید.</small>{active && operationId ? <button type="button" className="icon-button stop" onClick={() => void stop()} aria-label="توقف تولید"><Icon name="stop" /></button> : <button className="send-button" disabled={loading || active || !text.trim()} aria-label="ارسال پیام"><Icon name="send" /></button>}</div>
      </form>
    </aside>
    <main id="copilot-main" className={`choice-desk ${pane === 'desk' ? 'mobile-active' : ''}`} tabIndex={-1}>
      <div className="desk-intro"><p className="overline">میز انتخاب شما</p><h2>{hasNeed ? 'از نیاز روشن، به انتخاب مطمئن‌تر' : 'اول نیازت، بعد گزینه‌ها'}</h2><p>{hasNeed ? 'گفته‌های شما از شواهد محصول و قیمت جدا نگه داشته می‌شود.' : 'یک پیام کافی است. اینجا قدم‌به‌قدم نیاز خرید، گزینه‌ها و شواهد کنار هم قرار می‌گیرند.'}</p></div>
      {hasNeed && conversation && <BriefEditor key={`${conversation.id}:${conversation.brief_revision}`} conversation={conversation} onSaved={refresh} />}
      {!conversation?.brief.confirmed && <ol className="journey-steps"><li><span>۱</span><div><h3>نیازت را بگو</h3><p>برای چه کسی و چه کاری خرید می‌کنی؟</p></div></li><li><span>۲</span><div><h3>برداشت ما را تأیید کن</h3><p>بودجه و محدودیت‌ها همیشه دست خودت است.</p></div></li><li><span>۳</span><div><h3>گزینه‌ها را با شواهد ببین</h3><p>بدون قیمت یا مشخصات حدس‌زده‌شده.</p></div></li></ol>}
      {conversation && view === 'desk' && hasNeed && <details className="optional-tools"><summary>استفاده از شناخت ذخیره‌شدهٔ من</summary><MemorySuggestions key={`memory:${conversation.id}:${conversation.brief_revision}`} conversation={conversation} onSaved={refresh} /></details>}
      {conversation && hasNeed && <ChoiceDesk key={conversation.id} conversation={conversation} evidenceRevision={`${researchJob?.id ?? ''}:${researchJob?.completed ?? ''}`} />}
      {conversation?.brief.confirmed && <details className="research-ledger"><summary>از کجا بخرم؟</summary>
      <section className="research-panel" aria-labelledby="desk-title">
        <h2 id="desk-title">پیشنهادهای فروش و منابع</h2>
        <p className="research-scope">این بررسی فقط لینک‌های دقیق شما و منابع فعال را می‌بیند؛ پوشش همهٔ بازار یا قیمت نهایی تحویل را تضمین نمی‌کند.</p>
        <form className="research-form" onSubmit={startResearch}><label htmlFor="research-urls">لینک‌های دقیق محصول</label><textarea id="research-urls" value={researchUrls} onChange={(event) => setResearchUrls(event.target.value)} placeholder={'هر لینک HTTPS در یک خط؛ حداکثر ۳ لینک'} disabled={!conversation || researchBusy} /><button className="button primary" disabled={!conversation || researchBusy || !researchUrls.trim()}>بررسی پیشنهادها</button></form>
        {researchJob && <div className="research-progress" role="status"><span>{researchBusy ? 'در حال بررسی منابع…' : `بررسی ${researchJob.completed.toLocaleString('fa-IR')} از ${researchJob.total.toLocaleString('fa-IR')} منبع`}</span><progress max={Math.max(researchJob.total, 1)} value={researchJob.completed} /></div>}
        {researchJob?.offers.length ? <div className="offer-results"><div className="offer-heading"><div><p className="overline">مرتب‌شده بر پایه قیمت کالا</p><h3>کمترین قیمت بین منابع بررسی‌شده</h3></div><span>{researchJob.offers.length.toLocaleString('fa-IR')} پیشنهاد</span></div><div className="offer-list">{researchJob.offers.map((offer) => <article className="offer-card" key={offer.id}><div><span className={`evidence-badge ${offer.evidence_state.toLowerCase()}`}>{offer.evidence_state === 'LIVE' ? 'مشاهدهٔ زنده' : offer.evidence_state === 'CACHE' ? 'نسخهٔ ذخیره‌شده' : offer.evidence_state === 'STALE' ? 'قدیمی' : offer.evidence_state === 'CAPTURED_FIXTURE' ? 'ثبت واقعیِ تاریخی' : 'دادهٔ مصنوعی'}</span><h4>{offer.product_name}</h4><p>{offer.seller ?? 'فروشنده نامشخص'} · {offer.source_name}</p></div><strong>{offer.price_toman === null ? 'قیمت نامعلوم' : `${offer.price_toman.toLocaleString('fa-IR')} تومان`}</strong><dl><div><dt>موجودی</dt><dd>{offer.availability === 'IN_STOCK' ? 'موجود' : offer.availability === 'OUT_OF_STOCK' ? 'ناموجود' : 'نامعلوم'}</dd></div><div><dt>نوع مشاهده</dt><dd>{offer.observation_kind === 'MERCHANT_PAGE_VERIFIED' ? 'صفحهٔ فروشنده' : 'مشاهده در مقایسه‌گر'}</dd></div></dl><p className="unknown-cost">{offer.total_payable_toman === null ? 'هزینهٔ ارسال و مبلغ نهایی نامعلوم است.' : `مبلغ نهایی معلوم: ${offer.total_payable_toman.toLocaleString('fa-IR')} تومان`}</p><footer><time dateTime={offer.observed_at}>{new Date(offer.observed_at).toLocaleString('fa-IR')}</time>{(offer.merchant_url ?? offer.source_url) && <a href={offer.merchant_url ?? offer.source_url ?? '#'} target="_blank" rel="noreferrer">مشاهده منبع</a>}</footer></article>)}</div></div> : !researchJob && <div className="desk-empty compact"><div className="desk-orbit" aria-hidden="true"><Icon name="desk" /></div><h3>هنوز پیشنهادی بررسی نشده است.</h3><p>یک تا سه صفحهٔ دقیق از همان محصول را وارد کنید. اگر منبع در دسترس نباشد، قیمت حدس نمی‌زنیم.</p></div>}
        {researchJob && !researchBusy && !researchJob.offers.length && <div className="research-empty"><h3>پیشنهاد قابل‌نمایشی پیدا نشد.</h3><p>منابع بررسی‌شده اطلاعات کافی ندادند. قیمت یا موجودی ساخته نمی‌شود.</p><ul>{[...(researchJob.coverage.failed ?? []), ...(researchJob.coverage.blocked ?? [])].map((item) => <li key={`${item.source_id}-${item.code}`}><bdi>{item.source_id}</bdi>: اطلاعات این منبع در دسترس نیست.</li>)}</ul></div>}
      </section>
      </details>}
    </main>
    <nav className="mobile-switcher" aria-label="نمای موبایل"><button className={pane === 'conversation' ? 'active' : ''} onClick={() => setPane('conversation')}><Icon name="chat" />گفت‌وگو</button><button className={pane === 'desk' ? 'active' : ''} onClick={() => setPane('desk')}><Icon name="desk" />میز انتخاب</button></nav>
  </div></div>
}

function CategoryIcon({ kind }: { kind: string }) {
  const paths: Record<string, string> = {
    digital: 'M9 3h14v26H9z M14 25h4', appliance: 'M7 3h18v26H7z M7 12h18 M11 7v2 M11 17v5',
    living: 'M6 18V9h20v9 M3 16h6v9h14v-9h6v12H3z M7 28v3 M25 28v3',
    sport: 'm5 9 8 3 3 9 10 2 3 5H3v-7z M13 15l5-2 M15 19l5-2',
    gift: 'M4 13h24v6H4z M7 19v10h18V19 M16 13v16 M16 12C3 12 7 1 12 6z M16 12C29 12 25 1 20 6z',
    other: 'M5 10h22v19H5z M11 10V7a5 5 0 0 1 10 0v3',
  }
  return <svg aria-hidden="true" viewBox="0 0 32 34" width="36" height="38" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round"><path d={paths[kind]} /></svg>
}
