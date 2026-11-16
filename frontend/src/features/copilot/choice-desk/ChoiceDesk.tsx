import { useEffect, useRef, useState } from 'react'
import type { Conversation } from '../conversation/types'
import { choiceApi } from './api'
import type { Candidate, Choice, ChoiceItem } from './api'
import './choice-desk.css'
import { labels } from './labels'
import { ManualOffers, ObservedOffers, manualLabel } from './ManualOffers'
const label = (key: string) => labels[key] ?? key
const money = (value: number | null) => value === null ? 'نامعلوم' : `${value.toLocaleString('fa-IR')} تومان`
const valueText = (value: number | boolean | null) => value === null ? 'نامعلوم' : typeof value === 'boolean' ? value ? 'بله' : 'خیر' : value.toLocaleString('fa-IR')
const attribution = (value: string) => ({ USER_REPORTED: manualLabel, SYNTHETIC: 'دادهٔ مصنوعی آموزشی', CAPTURED_FIXTURE: 'ثبت واقعیِ تاریخی', VERIFIED_SOURCE: 'منبع بررسی‌شده' })[value] ?? 'نامعلوم'
const groupLabel = (value: string) => ({ SUPPORTED: 'سازگار با نیازهای معلوم', UNRESOLVED: 'نیازمند اطلاعات', INCOMPATIBLE: 'ناسازگار با شرط شما' })[value]
const outcomeLabel = (value: string) => ({ TIED: 'شواهد، برندهٔ یکتا نشان نمی‌دهند', SUPPORTED_CHOICE: 'یک انتخاب با پشتوانهٔ نیازهای معلوم', UNRESOLVED: 'اطلاعات برای تصمیم قطعی کافی نیست', NO_SUPPORTED_CHOICE: 'هیچ انتخاب سازگارِ پشتیبانی‌شده‌ای نداریم' })[value]

function EvidenceDrawer({ item, close }: { item: ChoiceItem; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    if (dialog.current?.showModal) dialog.current.showModal()
    else dialog.current?.setAttribute('open', '')
    dialog.current?.querySelector('button')?.focus()
    return () => previous?.focus()
  }, [])
  return <dialog ref={dialog} className="evidence-drawer" aria-labelledby="evidence-title" onCancel={close} onKeyDown={(e) => {
    if (e.key === 'Escape') close()
    if (e.key === 'Tab') {
      const controls = dialog.current?.querySelectorAll<HTMLElement>('button, a[href]')
      const first = controls?.[0]; const last = controls?.[controls.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus() }
    }
  }}>
    <button type="button" className="button ghost" onClick={close}>بستن منابع</button>
    <h2 id="evidence-title">شواهد <bdi>{item.name}</bdi></h2>
    <p>ادعای محصول از امتیاز فروشنده جداست؛ اینجا امتیاز فروشنده وارد رتبه‌بندی نشده است.</p>
    {item.sources.map((source) => <section key={source.id}>
      <h3>{source.label}</h3><p>{attribution(source.attribution)} — {source.fresh ? 'در بازهٔ تازگی ثبت‌شده' : 'قدیمی؛ فاقد اعتبار برای نتیجهٔ تازه'}</p>
      <p>زمان مشاهده: <time dateTime={source.observed_at}>{new Date(source.observed_at).toLocaleString('fa-IR')}</time></p>
      <p>اعتبار تا: <time dateTime={source.fresh_until}>{new Date(source.fresh_until).toLocaleString('fa-IR')}</time></p>
      {source.url && <a href={source.url} target="_blank" rel="noreferrer"><bdi>{source.url}</bdi></a>}
      <small>شناسهٔ snapshot: <bdi>{source.id}</bdi></small>
    </section>)}
    <h3>نیاز شما و شاهد متناظر</h3>
    {item.checks.length ? item.checks.map((check) => <p key={check.field}>{label(check.field)}: خواستهٔ شما {valueText(check.expected)}؛ شاهد {valueText(check.actual)}؛ {attribution(check.attribution)}<br /><small>شناسهٔ ادعا: <bdi>{check.evidence_id ?? 'وجود ندارد'}</bdi></small></p>) : <p>معیار مشخصی ثبت نشده؛ نتیجه فقط دربارهٔ بودجه و موجودی معلوم است.</p>}
  </dialog>
}

export function ChoiceDesk({ conversation, evidenceRevision = '' }: { conversation: Conversation; evidenceRevision?: string }) {
  const [choice, setChoice] = useState<Choice | null>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [intended, setIntended] = useState('')
  const [demoCategory, setDemoCategory] = useState(['electronics', 'home', 'sports'].includes(conversation.brief.category ?? '') ? conversation.brief.category! : 'electronics')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [drawer, setDrawer] = useState<ChoiceItem | null>(null)
  const active = useRef('')
  const stamp = `${conversation.id}:${conversation.brief_revision}:${conversation.brief.confirmed}`
  useEffect(() => {
    active.current = stamp
    let cancelled = false
    void Promise.all([choiceApi.get(conversation.id), choiceApi.candidates(conversation.id)]).then(([result, available]) => {
      if (!cancelled) {
        setChoice(result); setCandidates(available.items); setBusy(false); setDrawer(null)
        if (result) {
          setSelected((old) => old.length ? old : result.result.items.map((i) => i.id))
          setIntended((old) => old || result.result.items.find((i) => i.intended)?.id || '')
        }
      }
    }).catch(() => { if (!cancelled) setError('دریافت مقایسه انجام نشد؛ دوباره تلاش کنید.') })
    return () => { cancelled = true; active.current = '' }
  }, [conversation.id, stamp, evidenceRevision])
  useEffect(() => {
    if (!choice?.current || !choice.evidence_valid_until) return
    const delay = Math.max(0, Date.parse(choice.evidence_valid_until) - Date.now())
    const timer = window.setTimeout(() => setChoice((old) => old?.id === choice.id ? { ...old, current: false } : old), Math.min(delay, 2147483647))
    return () => window.clearTimeout(timer)
  }, [choice])
  const stale = !!choice && (!choice.current || choice.brief_revision !== conversation.brief_revision || !conversation.brief.confirmed)
  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError('')
    try { await action() } catch (reason) { if (active.current === stamp) setError(reason instanceof Error ? reason.message : 'درخواست انجام نشد.') }
    finally { if (active.current === stamp) setBusy(false) }
  }
  const demo = () => run(async () => {
    const data = await choiceApi.demo(conversation.id, conversation.brief_revision, demoCategory)
    const available = await choiceApi.candidates(conversation.id)
    if (active.current !== stamp) return
    setCandidates(available.items); setSelected(data.variant_ids); setIntended(data.variant_ids[0])
  })
  const recompute = () => run(async () => {
    const result = await choiceApi.compare(conversation.id, conversation.brief_revision, selected, intended)
    if (active.current === stamp) { setChoice(result); setDrawer(null) }
  })
  const result = stale ? null : choice?.result
  if (!conversation.brief.confirmed) return choice
    ? <p className="choice-notice" role="status">مقایسهٔ قبلی معتبر نیست؛ ابتدا نیاز اصلاح‌شده را تأیید کنید.</p>
    : null
  return <section className="personal-choice" aria-labelledby="comparison-title">
    <header className="choice-heading"><div><h2 id="comparison-title">گزینه‌های پیشنهادی</h2><p>مقایسه بر اساس نیاز تأییدشده و شواهد موجود؛ نه حدس مدل.</p></div><span className="choice-version">مقایسه</span></header>
    <ManualOffers key={stamp} conversationId={conversation.id} revision={conversation.brief_revision} category={conversation.brief.category ?? ''} candidates={candidates} onSaved={async id => {
      const available = await choiceApi.candidates(conversation.id)
      if (active.current !== stamp) return
      setCandidates(available.items); setSelected([id]); setIntended(id); setChoice(null)
    }} />
    <ObservedOffers candidates={candidates} />
    {!conversation.brief.confirmed && <p className="choice-notice">ابتدا برداشت از نیاز خرید را تأیید کنید.</p>}
    <details className="choice-controls" open={!choice}>
      <summary>محصول موردنظر و جایگزین‌ها</summary>
      <p>تا سه محصول جایگزین؛ فروشنده‌های یک محصول، جایگزین جداگانه نیستند.</p>
      <details><summary>آشنایی با مقایسه از طریق نمونهٔ آموزشی</summary><div className="demo-controls"><label>دستهٔ نمونهٔ آموزشی<select value={demoCategory} onChange={(e) => setDemoCategory(e.target.value)}><option value="electronics">الکترونیک</option><option value="home">خانه</option><option value="sports">ورزشی</option></select></label><button className="button ghost" disabled={busy || !conversation.brief.confirmed} onClick={() => void demo()}>بارگذاری دادهٔ مصنوعی</button></div></details>
      <p className="muted">نمونه‌ها ساختگی‌اند؛ قیمت و پوشش بازار زنده نیستند. دسته و معیار نیاز خرید باید با نمونه یکسان باشد.</p>
      {candidates.length > 0 && <><label>محصول موردنظر<select value={intended} onChange={(e) => { setIntended(e.target.value); setSelected([e.target.value]) }}><option value="">انتخاب کنید</option>{candidates.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><fieldset><legend>جایگزین‌های مقایسه</legend>{candidates.filter((item) => item.id !== intended && item.category === candidates.find((v) => v.id === intended)?.category).map((item) => <label className="choice-checkbox" key={item.id}><input type="checkbox" checked={selected.includes(item.id)} disabled={!selected.includes(item.id) && selected.length >= 4} onChange={(e) => setSelected(e.target.checked ? [...selected, item.id] : selected.filter((id) => id !== item.id))} /><bdi>{item.name}</bdi></label>)}</fieldset></>}
    </details>
    {stale && <p className="choice-notice" role="status">مقایسهٔ قبلی معتبر نیست؛ نیاز خرید تغییر کرده یا شواهد قدیمی‌اند. دوباره تأیید و مقایسه کنید.</p>}
    {error && <p role="alert" className="copilot-error">{error}</p>}
    <button className="button primary compare-button" disabled={busy || !conversation.brief.confirmed || !intended || !selected.length} onClick={() => void recompute()}>{busy ? 'در حال آماده‌سازی…' : 'ساخت مقایسه'}</button>
    {result && <>
      <div className="choice-verdict"><h3>{outcomeLabel(result.outcome)}</h3>{result.intent === 'ENJOYMENT' && <p>لذت‌بردن از خرید هدف معتبری است؛ تناسب را با نیاز و بودجهٔ خودتان می‌سنجیم.</p>}{result.clarification && <p>{result.clarification}</p>}{result.no_alternatives && <p>جایگزین پشتیبانی‌شده‌ای در این مقایسه نداریم.</p>}</div>
      <table className="choice-summary"><caption>خلاصهٔ مقایسهٔ محصولات، نه فروشندگان</caption><thead><tr><th scope="col">محصول</th><th scope="col">وضعیت</th><th scope="col">هزینهٔ نهایی</th><th scope="col">پوشش معلوم</th></tr></thead><tbody>{result.items.map((item) => <tr key={item.id}><th scope="row"><bdi>{item.name}</bdi></th><td>{groupLabel(item.group)}</td><td>{money(item.total)}</td><td>{item.coverage.known.toLocaleString('fa-IR')} از {item.coverage.total.toLocaleString('fa-IR')}</td></tr>)}</tbody></table>
      <div className="comparison-cards">{result.items.map((item) => <article className={`comparison-card ${item.group.toLowerCase()}`} key={item.id}>
        <div className="choice-card-heading"><span>{item.intended ? 'محصول موردنظر شما' : 'محصول جایگزین'}</span><span>{groupLabel(item.group)}</span></div>
        <h3><bdi>{item.name}</bdi></h3>
        <div className="choice-provenance">{[...new Set(item.sources.map((s) => attribution(s.attribution)))].join('، ')}</div>
        <p className="choice-price">{item.total === null ? `قیمت کالا: ${money(item.item_price)} — هزینهٔ نهایی نامعلوم` : `هزینهٔ نهایی معلوم: ${money(item.total)}`}</p>
        <h4>چرا به نیاز شما می‌خورد؟</h4>
        <p>{item.cost_state === 'WITHIN_BUDGET_CONFIRMED' ? 'هزینهٔ نهایی در سقف بودجهٔ شماست.' : item.cost_state === 'ABOVE_BUDGET' ? 'هزینه از بودجهٔ بیان‌شده بیشتر است.' : 'تناسب با بودجه هنوز قطعی نیست.'}</p>
        {item.checks.filter((c) => c.result === 'SATISFIED').map((c) => <p key={c.field}>{label(c.field)}: {valueText(c.actual)}؛ مطابق خواستهٔ شما.</p>)}
        <h4>چه چیزی را از دست می‌دهید؟</h4>
        {item.tradeoffs.length ? item.tradeoffs.map((key) => { const check = item.checks.find((c) => c.field === key); return <p key={key}>{check ? `${label(key)}: شما ${valueText(check.expected)} خواسته‌اید؛ شاهد این محصول ${valueText(check.actual)} است.` : label(key)}</p> }) : <p>ناسازگاری معلومی در معیارهای بررسی‌شده ثبت نشده؛ این به معنی بی‌نقص‌بودن نیست.</p>}
        <details><summary>نامعلوم‌ها و آنچه می‌تواند نتیجه را تغییر دهد</summary><p>{item.unknowns.length ? item.unknowns.map(label).join('، ') : 'در معیارهای بررسی‌شده نامعلومی ثبت نشده است.'}</p><p>نتیجه با روشن‌شدن {item.would_change_if.map(label).join('، ')} ممکن است تغییر کند.</p></details>
        <p className="coverage">پوشش: {item.coverage.known.toLocaleString('fa-IR')} از {item.coverage.total.toLocaleString('fa-IR')} مورد معلوم؛ {item.sources.every((s) => s.fresh) ? 'شواهد در بازهٔ تازگی' : 'بخشی از شواهد قدیمی است'}</p>
        <button className="text-button" onClick={() => setDrawer(item)}>شواهد و منابع <span className="sr-status">{item.name}</span></button>
        <details><summary>پیشنهادهای فروش همین محصول ({item.offers.length.toLocaleString('fa-IR')})</summary><p>مرتب‌سازی قیمت کالا فقط در همین variant؛ هزینهٔ نهایی نامعلوم با قیمت کالا یکسان نیست.</p>{[...item.offers].sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity) || a.id.localeCompare(b.id)).map((offer) => <div className="attached-offer" key={offer.id}><strong>{offer.seller ?? 'فروشنده نامعلوم'}</strong><p>{money(offer.price)}؛ ارسال: {money(offer.shipping)}؛ هزینهٔ اجباری: {money(offer.mandatory)}</p><p>{attribution(offer.attribution)}؛ {offer.observation_kind === 'USER_REPORTED' ? 'مشاهدهٔ اعلامی کاربر' : offer.observation_kind === 'COMPARISON_OBSERVED' ? 'مشاهده در مقایسه‌گر، نه تأیید فروشنده' : 'مشاهدهٔ صفحهٔ فروشنده'}؛ {offer.fresh ? 'در بازهٔ تازگی' : 'قدیمی'}</p><p>موجودی: {offer.stock === 'IN_STOCK' ? 'موجود' : offer.stock === 'OUT_OF_STOCK' ? 'ناموجود' : 'نامعلوم'}؛ <time dateTime={offer.observed_at}>{new Date(offer.observed_at).toLocaleString('fa-IR')}</time></p>{offer.url && <a href={offer.url} target="_blank" rel="noreferrer">صفحهٔ پیشنهاد</a>}</div>)}</details>
      </article>)}</div>
      <p className="conditional-path">اگر هیچ گزینه‌ای شرط شما را برآورده نمی‌کند، خرید را تا روشن‌شدن شواهد نگه دارید یا یک variant دارای شاهد را انتخاب کنید؛ هزینهٔ تعمیر، تخفیف آینده یا موجودی دست‌دوم فرض نشده است.</p>
    </>}
    {drawer && !stale && <EvidenceDrawer item={drawer} close={() => setDrawer(null)} />}
  </section>
}
