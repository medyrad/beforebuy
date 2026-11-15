import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

import { copilotApi, CopilotApiError, newIdempotencyKey } from './api'
import { Icon } from './Icons'
import type { Conversation, ConversationSummary, OperationStatus, ResearchJob, Upload } from './types'
import { ChoiceDesk } from '../choice-desk/ChoiceDesk'
import { ComparisonProfile } from '../choice-desk/ComparisonProfile'

type MobilePane = 'conversation' | 'desk'

const errorText = (error: unknown) => error instanceof CopilotApiError ? error.message : 'ارتباط برقرار نشد؛ دوباره تلاش کنید.'

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
    <div><p className="overline">brief نسخهٔ {conversation.brief_revision.toLocaleString('fa-IR')}</p><h2 id="brief-title">آنچه فعلاً قطعی است</h2></div>
    <div className="brief-chips">
      <span>{conversation.brief.recipient_context === 'GIFT' ? 'برای هدیه' : conversation.brief.recipient_context === 'HOUSEHOLD' ? 'برای خانه' : conversation.brief.recipient_context === 'SELF' ? 'برای خودم' : 'مخاطب نامعلوم'}</span>
      <span>{conversation.brief.category ?? 'دسته نامعلوم'}</span>
      <span>{conversation.brief.budget_toman === null ? 'بودجه نامعلوم' : `${conversation.brief.budget_toman.toLocaleString('fa-IR')} تومان`}</span>
    </div>
    <div className="brief-actions"><button className="text-button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>ویرایش brief</button>{!conversation.brief.confirmed && <button className="text-button confirm" disabled={busy} onClick={() => void confirm()}>تأیید brief برای پژوهش</button>}</div>
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
      if (researchTimerRef.current !== null) window.clearTimeout(researchTimerRef.current)
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

  const pollResearch = async (jobId: string) => {
    try {
      const next = await copilotApi.research(jobId)
      setResearchJob(next)
      if (['PENDING', 'RUNNING'].includes(next.status)) researchTimerRef.current = window.setTimeout(() => void pollResearch(jobId), 750)
      else setResearchBusy(false)
    } catch (reason) { setResearchBusy(false); setError(errorText(reason)) }
  }

  const startResearch = async (event: FormEvent) => {
    event.preventDefault()
    if (!conversation) return
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
      setResearchJob(accepted.job)
      if (['PENDING', 'RUNNING'].includes(accepted.job.status)) await pollResearch(accepted.job.id)
      else setResearchBusy(false)
    } catch (reason) {
      setResearchBusy(false)
      setError(reason instanceof Error && reason.message === 'invalid' ? 'لینک باید HTTPS و بدون query یا fragment باشد.' : errorText(reason))
    }
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
      {conversation && <BriefEditor key={`${conversation.id}:${conversation.brief_revision}`} conversation={conversation} onSaved={refresh} />}
      {conversation && <ChoiceDesk key={conversation.id} conversation={conversation} evidenceRevision={`${researchJob?.id ?? ''}:${researchJob?.completed ?? ''}`} />}
      <details className="research-ledger"><summary>پژوهش منابع و پیشنهادهای فروش</summary>
      <section className="research-panel" aria-labelledby="desk-title">
        <p className="overline">Choice Desk · پایلوت محدود</p><h2 id="desk-title">پیشنهادهای واقعی و منبع‌دار</h2>
        <p className="research-scope">این بررسی فقط لینک‌های دقیق شما و منابع فعال را می‌بیند؛ پوشش همهٔ بازار یا قیمت نهایی تحویل را تضمین نمی‌کند.</p>
        <form className="research-form" onSubmit={startResearch}><label htmlFor="research-urls">لینک‌های دقیق محصول</label><textarea id="research-urls" value={researchUrls} onChange={(event) => setResearchUrls(event.target.value)} placeholder={'هر لینک HTTPS در یک خط؛ حداکثر ۳ لینک'} disabled={!conversation || researchBusy} /><button className="button primary" disabled={!conversation || researchBusy || !researchUrls.trim()}>بررسی پیشنهادها</button></form>
        {researchJob && <div className="research-progress" role="status"><span>{researchBusy ? 'در حال بررسی منابع…' : `بررسی ${researchJob.completed.toLocaleString('fa-IR')} از ${researchJob.total.toLocaleString('fa-IR')} منبع`}</span><progress max={Math.max(researchJob.total, 1)} value={researchJob.completed} /></div>}
        {researchJob?.offers.length ? <div className="offer-results"><div className="offer-heading"><div><p className="overline">مرتب‌شده بر پایه قیمت کالا</p><h3>کمترین قیمت بین منابع بررسی‌شده</h3></div><span>{researchJob.offers.length.toLocaleString('fa-IR')} پیشنهاد</span></div><div className="offer-list">{researchJob.offers.map((offer) => <article className="offer-card" key={offer.id}><div><span className={`evidence-badge ${offer.evidence_state.toLowerCase()}`}>{offer.evidence_state === 'LIVE' ? 'مشاهدهٔ زنده' : offer.evidence_state === 'CACHE' ? 'نسخهٔ ذخیره‌شده' : offer.evidence_state === 'STALE' ? 'قدیمی' : offer.evidence_state === 'CAPTURED_FIXTURE' ? 'ثبت واقعیِ تاریخی' : 'دادهٔ مصنوعی'}</span><h4>{offer.product_name}</h4><p>{offer.seller ?? 'فروشنده نامشخص'} · {offer.source_name}</p></div><strong>{offer.price_toman === null ? 'قیمت نامعلوم' : `${offer.price_toman.toLocaleString('fa-IR')} تومان`}</strong><dl><div><dt>موجودی</dt><dd>{offer.availability === 'IN_STOCK' ? 'موجود' : offer.availability === 'OUT_OF_STOCK' ? 'ناموجود' : 'نامعلوم'}</dd></div><div><dt>نوع مشاهده</dt><dd>{offer.observation_kind === 'MERCHANT_PAGE_VERIFIED' ? 'صفحهٔ فروشنده' : 'مشاهده در مقایسه‌گر'}</dd></div></dl><p className="unknown-cost">{offer.total_payable_toman === null ? 'هزینهٔ ارسال و مبلغ نهایی نامعلوم است.' : `مبلغ نهایی معلوم: ${offer.total_payable_toman.toLocaleString('fa-IR')} تومان`}</p><footer><time dateTime={offer.observed_at}>{new Date(offer.observed_at).toLocaleString('fa-IR')}</time>{(offer.merchant_url ?? offer.source_url) && <a href={offer.merchant_url ?? offer.source_url ?? '#'} target="_blank" rel="noreferrer">مشاهده منبع</a>}</footer></article>)}</div></div> : !researchJob && <div className="desk-empty compact"><div className="desk-orbit" aria-hidden="true"><Icon name="desk" /></div><h3>هنوز پیشنهادی بررسی نشده است.</h3><p>یک تا سه صفحهٔ دقیق از همان محصول را وارد کنید. failure منبع با fixture جایگزین نمی‌شود.</p></div>}
        {researchJob && !researchBusy && !researchJob.offers.length && <div className="research-empty"><h3>پیشنهاد قابل‌نمایشی پیدا نشد.</h3><p>وضعیت اجرا: {researchJob.status}. failure زنده با fixture جایگزین نشده است.</p><ul>{[...(researchJob.coverage.failed ?? []), ...(researchJob.coverage.blocked ?? [])].map((item) => <li key={`${item.source_id}-${item.code}`}>{item.source_id}: {item.code}</li>)}</ul></div>}
      </section>
      </details>
    </main>
    <nav className="mobile-switcher" aria-label="نمای موبایل"><button className={pane === 'conversation' ? 'active' : ''} onClick={() => setPane('conversation')}><Icon name="chat" />گفت‌وگو</button><button className={pane === 'desk' ? 'active' : ''} onClick={() => setPane('desk')}><Icon name="desk" />میز انتخاب</button></nav>
  </div>
}
