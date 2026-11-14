import type { AnalysisSummary } from '../../services/api/types'
import { faLabel } from '../analysis/labels'

interface Props {
  items: AnalysisSummary[]
  loading: boolean
  error: string | null
  onOpen: (id: string) => void
  onDelete: (id: string) => void
  onClear: () => void
}

const date = new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium' })

export function HistoryView({ items, loading, error, onOpen, onDelete, onClear }: Props) {
  if (loading) return <div className="state-card" role="status"><span className="spinner" />در حال دریافت تاریخچه…</div>
  if (error) return <div className="state-card error" role="alert"><h2>دریافت تاریخچه ممکن نشد</h2><p>{error}</p></div>
  if (!items.length) return <div className="state-card empty"><p className="eyebrow">تاریخچه</p><h1>هنوز تحلیلی ندارید</h1><p>تحلیل‌ها فقط با اطلاعات مهمان همین مرورگر در دسترس‌اند. خالی‌بودن فهرست می‌تواند به‌علت نشست تازه، انقضا یا پاک‌شدن داده باشد.</p></div>

  return <section aria-labelledby="history-title">
    <div className="section-heading"><div><p className="eyebrow">ذخیره‌شده در همین مرورگر</p><h1 id="history-title">تاریخچهٔ تحلیل‌ها</h1></div><button type="button" className="button danger-quiet" onClick={() => { if (window.confirm('همهٔ تحلیل‌های این مرورگر پاک شوند؟ این کار بازگشت‌پذیر نیست.')) onClear() }}>پاک‌کردن همهٔ تاریخچه</button></div>
    <div className="history-list">
      {items.map((item) => <article className="history-item" key={item.id}>
        <button className="history-open" type="button" onClick={() => onOpen(item.id)}><span className="history-title"><bdi dir="auto">{item.product_label}</bdi></span><span>{faLabel(item.primary_outcome)}</span><span className="history-date">{date.format(new Date(item.created_at))}</span></button>
        <button className="icon-button" type="button" aria-label={`حذف تحلیل ${item.product_label}`} onClick={() => { if (window.confirm('این تحلیل پاک شود؟')) onDelete(item.id) }}>حذف</button>
      </article>)}
    </div>
  </section>
}
