import type { Analysis } from '../../services/api/types'
import { faLabel } from './labels'

interface Props {
  analysis: Analysis
  onEdit: () => void
  onRetry: () => void
  onRate: (rating: number) => void
  onRemoveRating: () => void
  pendingAction: string | null
}

const number = new Intl.NumberFormat('fa-IR')
const date = new Intl.DateTimeFormat('fa-IR', { dateStyle: 'long' })

export function ReportView({ analysis, onEdit, onRetry, onRate, onRemoveRating, pendingAction }: Props) {
  const { report } = analysis
  const mode = report.mode === 'MOCK_ASSISTED'
    ? { title: 'نسخهٔ نمایشی', detail: 'توضیح این گزارش با مولد آزمایشی ساخته شده است؛ هوش مصنوعی زنده نیست.', className: 'mock' }
    : report.mode === 'RULE_BASED_LIMITED'
      ? { title: 'گزارش محدود', detail: 'توضیح هوشمند در دسترس نبود؛ جمع‌بندی اصلی همچنان معتبر است.', className: 'limited' }
      : { title: 'توضیح هوش مصنوعی', detail: 'هوش مصنوعی فقط توضیح تکمیلی را نوشته است؛ جمع‌بندی اصلی تغییر نمی‌کند.', className: 'live' }

  const cards = [
    ['دلیل خرید یا تعویض', report.dimensions.justification],
    ['تناسب با بودجه', report.dimensions.budget],
    ['مناسب‌بودن مدل', report.dimensions.target_fit],
    ['بررسی محدودیت‌ها', report.dimensions.tradeoff],
  ] as const
  const reasons = report.explanation_blocks.filter((block) => block.kind !== 'ai_context')
  const aiContext = report.explanation_blocks.filter((block) => block.kind === 'ai_context')

  return <article className="report" aria-labelledby="report-title">
    <header className="report-hero">
      <div className="report-kicker"><span className={`mode-badge ${mode.className}`} role="status">{mode.title}</span><span>{mode.detail}</span></div>
      <p className="eyebrow">تحلیل برای <bdi dir="auto">{analysis.product_label}</bdi></p>
      <h1 id="report-title">{faLabel(report.primary_outcome)}</h1>
      {report.headline_fa && <p className="report-explanation">{report.headline_fa}</p>}
      {report.unknowns.includes('TARGET_MODEL_CAPABILITY') && <p className="unknown-callout"><strong>نکتهٔ مهم:</strong> مشخصات فنی این مدل تأیید نشده است. این ابهام ارزیابی دلیل خرید یا بودجه را منفی نمی‌کند.</p>}
    </header>

    <section aria-labelledby="dimensions-title">
      <div className="section-heading compact-heading"><div><p className="eyebrow">چهار بخش تصمیم</p><h2 id="dimensions-title">جمع‌بندی برای تصمیم شما</h2></div></div>
      <div className="dimension-grid">
        {cards.map(([title, value]) => <div className="dimension-card" key={title}><h3>{title}</h3><p>{faLabel(value)}</p></div>)}
      </div>
    </section>

    <div className="report-details">
      <section className="detail-card" aria-labelledby="reasons-title">
        <h2 id="reasons-title">دلیل‌های پشتیبان</h2>
        {reasons.length ? <ul>{reasons.map((block, index) => <li key={`${block.text_fa}-${index}`}>{block.text_fa}</li>)}</ul> : <p>از پاسخ‌های فعلی دلیل تکمیلی دیگری به دست نیامد.</p>}
        {aiContext.length > 0 && <><h3>توضیح تکمیلی</h3><ul>{aiContext.map((block, index) => <li key={`${block.text_fa}-${index}`}>{block.text_fa}</li>)}</ul></>}
        <p className="money-summary">قیمت واردشده: <strong>{number.format(analysis.price_toman)} تومان</strong><br />بودجه: <strong>{analysis.budget_toman === null ? 'نامعلوم' : `${number.format(analysis.budget_toman)} تومان`}</strong></p>
      </section>
      <section className="detail-card" aria-labelledby="actions-title">
        <h2 id="actions-title">قدم‌های بعدی</h2>
        {report.actions.length ? <ul>{report.actions.map((action) => <li key={action}>{faLabel(action)}</li>)}</ul> : <p>اقدام تکمیلی مشخصی از پاسخ‌ها به دست نیامد.</p>}
        {report.unknowns.length > 0 && <><h3>موارد نامعلوم</h3><ul>{report.unknowns.map((item) => <li key={item}>{faLabel(item)}</li>)}</ul></>}
      </section>
    </div>

    <section className="feedback-card" aria-labelledby="feedback-title">
      <div><h2 id="feedback-title">این تحلیل چقدر به تصمیم شما کمک کرد؟</h2><p>اختیاری است و فقط برای همین نسخه ثبت می‌شود.</p></div>
      <fieldset disabled={pendingAction === 'feedback'}><legend className="sr-only">امتیاز مفیدبودن</legend><div className="rating-row">{[1, 2, 3, 4, 5].map((rating) => {
        const endpoint = rating === 1 ? '، اصلاً کمک نکرد' : rating === 5 ? '، خیلی کمک کرد' : ''
        return <label key={rating}><input type="radio" name="rating" aria-label={`${number.format(rating)}${endpoint}`} checked={report.feedback?.rating === rating} onChange={() => onRate(rating)} /><span>{number.format(rating)}</span></label>
      })}</div><div className="rating-scale" aria-hidden="true"><span dir="rtl">اصلاً کمک نکرد</span><span dir="rtl">خیلی کمک کرد</span></div></fieldset>
      {report.feedback && <button className="text-button" type="button" onClick={onRemoveRating} disabled={pendingAction === 'feedback'}>حذف امتیاز</button>}
    </section>

    <footer className="report-footer">
      <p>این تحلیل تا {date.format(new Date(analysis.expires_at))} در همین مرورگر قابل دسترسی است؛ پاک‌شدن cookie می‌تواند دسترسی را زودتر از بین ببرد.</p>
      <div className="button-row"><button className="button secondary" type="button" onClick={onEdit}>اصلاح پاسخ‌ها</button><button className="button ghost" type="button" onClick={onRetry} disabled={pendingAction === 'retry'}>{pendingAction === 'retry' ? 'در حال تحلیل دوباره…' : 'تحلیل دوباره'}</button></div>
    </footer>
  </article>
}
