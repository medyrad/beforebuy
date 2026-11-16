import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { choiceApi } from './api'
import type { Candidate } from './api'

export const manualLabel = 'واردشده توسط کاربر؛ مستقلاً تأیید نشده'
const fields = { brand: 'برند', model_name: 'نام دقیق محصول', model_code: 'کد مدل سازنده', capacity: 'ظرفیت نسخه', size: 'اندازهٔ نسخه', year: 'سال مدل', region: 'منطقهٔ عرضه', warranty: 'گارانتی نسخه' }
const amountText = (v: number | null | undefined) => v == null ? 'نامعلوم' : `${v.toLocaleString('fa-IR')} تومان`
const initialIdentity = (category: string) => ({ brand: '', model_name: '', model_code: '', category: ['electronics', 'home', 'sports'].includes(category) ? category : 'electronics', capacity: 'UNKNOWN', size: 'UNKNOWN', year: 'UNKNOWN', region: 'UNKNOWN', warranty: 'UNKNOWN', condition: 'UNKNOWN', bundle: 'UNKNOWN' })

export function ManualOffers({ conversationId, revision, category, candidates, onSaved }: {
  conversationId: string; revision: number; category: string; candidates: Candidate[]; onSaved: (id: string) => void | Promise<void>
}) {
  const [identity, setIdentity] = useState<Record<string, string>>(() => initialIdentity(category))
  const [variant, setVariant] = useState(''); const [confirmed, setConfirmed] = useState(false)
  const [seller, setSeller] = useState(''); const [url, setUrl] = useState('')
  const [amount, setAmount] = useState(''); const [currency, setCurrency] = useState('TOMAN')
  const [shipping, setShipping] = useState(''); const [mandatory, setMandatory] = useState('')
  const [observed, setObserved] = useState(''); const [stock, setStock] = useState('UNKNOWN')
  const [busy, setBusy] = useState(false); const [notice, setNotice] = useState('')
  const locked = useRef(false); const active = useRef(true)
  useEffect(() => { active.current = true; return () => { active.current = false } }, [])
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (locked.current) return
    locked.current = true; setBusy(true); setNotice('')
    try {
      const result = await choiceApi.manual(conversationId, { expected_revision: revision, identity, variant_id: variant || null,
        same_variant_confirmed: confirmed, seller, source_url: url, amount: amount || null, currency,
        shipping_toman: shipping || null, mandatory_toman: mandatory || null, availability: stock,
        observed_at: new Date(observed).toISOString() })
      if (!active.current) return
      await onSaved(result.variant_id)
      if (!active.current) return
      setVariant(result.variant_id); setConfirmed(false); setSeller(''); setUrl(''); setAmount(''); setShipping(''); setMandatory(''); setStock('UNKNOWN'); setObserved('')
      setNotice('پیشنهاد ثبت شد؛ ' + manualLabel)
    } catch (e) { if (active.current) setNotice(e instanceof Error ? e.message : 'ثبت انجام نشد؛ دوباره تلاش کنید.') }
    finally { if (active.current) { locked.current = false; setBusy(false) } }
  }
  return <details className="manual-offers"><summary>ثبت پیشنهادی که خودم دیده‌ام</summary>
    <p>{manualLabel}. وقتی بررسی خودکار در دسترس نیست، اطلاعات صفحه‌ای را که خودتان دیده‌اید ثبت کنید؛ قیمت نمونه وارد نکنید. این کار هیچ سایتی را واکشی نمی‌کند.</p>
    <form onSubmit={event => void submit(event)}>
      <fieldset disabled={busy} className="manual-grid"><legend>محصول و نسخهٔ دقیق</legend>
        <label>نسخهٔ مورد مقایسه<select value={variant} onChange={e => { const id = e.target.value; setVariant(id); setConfirmed(false); setIdentity(id ? { ...candidates.find(c => c.id === id)!.identity! } : initialIdentity(category)) }}>
          <option value="">محصول یا نسخهٔ جدید</option>{candidates.filter(c => c.sources.some(s => s.attribution === 'USER_REPORTED')).map(c => <option key={c.id} value={c.id}>{c.name} — {c.identity?.size} — {c.identity?.capacity}</option>)}
        </select></label>
        <label>دستهٔ پیشنهاد<select value={identity.category} disabled={!!variant} onChange={e => setIdentity({ ...identity, category: e.target.value })}><option value="electronics">الکترونیک</option><option value="home">خانه</option><option value="sports">ورزشی</option></select></label>
        {Object.entries(fields).map(([key, label]) => <label key={key}>{label}<input required maxLength={120} value={identity[key] ?? ''} readOnly={!!variant} onChange={e => setIdentity({ ...identity, [key]: e.target.value })} /></label>)}
        <label>وضعیت کالا<select disabled={!!variant} value={identity.condition} onChange={e => setIdentity({ ...identity, condition: e.target.value })}><option value="UNKNOWN">نامعلوم</option><option value="NEW">نو</option><option value="USED">کارکرده</option><option value="REFURBISHED">بازسازی‌شده</option></select></label>
        <label>بستهٔ همراه<select disabled={!!variant} value={identity.bundle} onChange={e => setIdentity({ ...identity, bundle: e.target.value })}><option value="UNKNOWN">نامعلوم</option><option value="NO">بدون بستهٔ اضافه</option><option value="YES">با بستهٔ اضافه</option></select></label>
        <p>UNKNOWN یعنی نامعلوم، نه یکسان‌بودن واقعی. نسخه‌های متفاوت را جدا ثبت کنید؛ به شباهت نام اکتفا نکنید.</p>
        {variant && <label className="choice-checkbox"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />این پیشنهاد را برای همین نسخه با ویژگی‌های نمایش‌داده‌شده ثبت می‌کنم؛ موارد نامعلوم تأیید فنی نشده‌اند.</label>}
      </fieldset>
      <fieldset disabled={busy} className="manual-grid"><legend>پیشنهاد مشاهده‌شده</legend>
        <label>فروشنده<input required maxLength={200} value={seller} onChange={e => setSeller(e.target.value)} /></label>
        <label>لینک صفحهٔ پیشنهاد<input required type="url" dir="ltr" maxLength={1000} value={url} onChange={e => setUrl(e.target.value)} /></label>
        <label>قیمت مشاهده‌شده<input inputMode="numeric" value={amount} onChange={e => setAmount(e.target.value)} placeholder="خالی یعنی نامعلوم" /></label>
        <label>واحد مبلغ اصلی<select value={currency} onChange={e => setCurrency(e.target.value)}><option value="TOMAN">تومان</option><option value="IRR">ریال — هر ۱۰ ریال یک تومان</option></select></label>
        <label>هزینهٔ ارسال (تومان)<input inputMode="numeric" value={shipping} onChange={e => setShipping(e.target.value)} placeholder="خالی یعنی نامعلوم" /></label>
        <label>هزینه‌های اجباری (تومان)<input inputMode="numeric" value={mandatory} onChange={e => setMandatory(e.target.value)} placeholder="صفر فقط اگر معلوم است" /></label>
        <label>موجودی مشاهده‌شده<select value={stock} onChange={e => setStock(e.target.value)}><option value="UNKNOWN">نامعلوم</option><option value="IN_STOCK">موجود</option><option value="OUT_OF_STOCK">ناموجود</option><option value="PREORDER">پیش‌فروش</option></select></label>
        <label>زمان مشاهدهٔ شما<input required type="datetime-local" value={observed} onChange={e => setObserved(e.target.value)} /></label>
      </fieldset>
      <button className="button primary" disabled={busy || (!!variant && !confirmed)}>{busy ? 'در حال ثبت…' : 'ثبت پیشنهاد دستی'}</button>
      {notice && <p role="status">{notice}</p>}
    </form>
  </details>
}

export function ObservedOffers({ candidates }: { candidates: Candidate[] }) {
  const real = candidates.filter(c => c.sources.some(s => ['USER_REPORTED', 'VERIFIED_SOURCE'].includes(s.attribution)))
  if (!real.length) return null
  return <section aria-label="مقایسهٔ قیمت‌های ثبت‌شده"><h3>مقایسهٔ پیشنهادهای ثبت‌شده</h3>
    <p>فقط نسخهٔ یکسان؛ دادهٔ دستی شرطی بر اعلام شماست و توصیهٔ فنی نیست. شاهد کافی برای پیشنهاد محصول جایگزین نداریم؛ مشخصات معتبرِ معیارهای نیاز و پیشنهاد فروش تاریخ‌دار لازم است.</p>
    {real.map(c => {
      const offers = [...c.offers].sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity) || a.id.localeCompare(b.id))
      const usable = offers.filter(o => o.fresh && o.stock === 'IN_STOCK' && !o.conflicting)
      const prices = usable.flatMap(o => o.price == null ? [] : [o.price]); const totals = usable.flatMap(o => o.total == null ? [] : [o.total])
      return <article key={c.id} className="observed-product"><h4><bdi>{c.name}</bdi></h4>
        {c.identity && <p>نسخهٔ اعلامی: {Object.entries(c.identity).map(([k, v]) => `${({ ...fields, category: 'دسته', condition: 'وضعیت', bundle: 'بسته' } as Record<string, string>)[k] ?? k}: ${v === 'UNKNOWN' ? 'نامعلوم' : v}`).join('؛ ')}</p>}
        <p>کمترین قیمت کالای موجود و تازهٔ بدون تعارض در این گروه: {amountText(prices.length ? Math.min(...prices) : null)}؛ کمترین مبلغ نهایی با اجزای معلوم: {amountText(totals.length ? Math.min(...totals) : null)}</p>
        {offers.map(o => <div key={o.id} className="attached-offer"><strong>{o.seller}</strong><p>{o.attribution === 'USER_REPORTED' ? manualLabel : o.observation_kind === 'COMPARISON_OBSERVED' ? 'مشاهده در مقایسه‌گر؛ فروشنده مستقلاً تأیید نشده' : 'مشاهدهٔ صفحهٔ فروشنده'}</p>
          <p>قیمت کالا: {amountText(o.price)}؛ مبلغ نهایی: {amountText(o.total)}</p><p>ارسال: {amountText(o.shipping)}؛ هزینه‌های اجباری: {amountText(o.mandatory)}</p>
          <p>مبلغ اصلی: {o.original_amount?.toLocaleString('fa-IR') ?? 'نامعلوم'} {o.original_currency === 'IRR' ? 'ریال' : 'تومان'}؛ {o.stock === 'IN_STOCK' ? 'موجود' : o.stock === 'OUT_OF_STOCK' ? 'ناموجود' : o.stock === 'PREORDER' ? 'پیش‌فروش' : 'موجودی نامعلوم'}؛ {o.fresh ? 'در بازهٔ تازگی' : 'قدیمی — برای قیمت فعلی بررسی شود'}</p>
          {o.conflicting && <p role="status">مشاهدات این فروشنده تعارض دارند؛ پیش از خرید بررسی کنید.</p>}
          <p>زمان مشاهده: <time dateTime={o.observed_at}>{new Date(o.observed_at).toLocaleString('fa-IR')}</time>{o.entered_at && <>؛ زمان ثبت در برنامه: <time dateTime={o.entered_at}>{new Date(o.entered_at).toLocaleString('fa-IR')}</time></>}</p>
          {o.url && <a href={o.url} target="_blank" rel="noopener noreferrer">بازکردن صفحهٔ فروشنده یا منبع (خارج از برنامه)</a>}
        </div>)}
      </article>
    })}
  </section>
}
