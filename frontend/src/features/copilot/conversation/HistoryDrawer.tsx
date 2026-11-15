import { useEffect, useRef, useState } from 'react'
import { copilotApi } from './api'
import type { ConversationSummary } from './types'

export function HistoryDrawer({ close, open, fresh, deleted }: {
  close: () => void; open: (id: string) => Promise<void>; fresh: () => void
  deleted: (id?: string) => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [items, setItems] = useState<ConversationSummary[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState<string | null>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const element = dialog.current
    if (dialog.current?.showModal) dialog.current.showModal()
    else dialog.current?.setAttribute('open', '')
    let active = true
    void copilotApi.list().then((data) => { if (active) { setItems(data.items); setCursor(data.next_cursor) } })
      .catch(() => { if (active) setError('دریافت گفت‌وگوها انجام نشد. پنجره را ببندید و دوباره باز کنید.') })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false; element?.close?.(); previous?.focus() }
  }, [])
  const remove = async () => {
    if (!confirm || busy) return
    setBusy(true); setError('')
    try {
      if (confirm === 'all') { await copilotApi.clear(); setItems([]); setCursor(null); deleted() }
      else { await copilotApi.remove(confirm); setItems((old) => old.filter((i) => i.id !== confirm)); deleted(confirm) }
      setConfirm(null)
    } catch { setError('حذف انجام نشد؛ ممکن است گفت‌وگو منقضی شده باشد. دوباره تلاش کنید.') }
    finally { setBusy(false) }
  }
  return <dialog ref={dialog} className="history-drawer" aria-labelledby="history-heading" onKeyDown={(e) => { if (e.key === 'Escape' && !busy) { e.preventDefault(); close() } }} onCancel={(e) => { e.preventDefault(); if (!busy) close() }}>
    <header><h2 id="history-heading">گفت‌وگوهای من</h2><button onClick={close} disabled={busy} aria-label="بستن تاریخچه">×</button></header>
    <p>فقط در این مرورگر؛ گفت‌وگوهای منقضی‌شده نمایش داده نمی‌شوند.</p>
    <button className="button primary" disabled={busy} onClick={() => { fresh(); close() }}>گفت‌وگوی تازه</button>
    <label>جست‌وجو در عنوان‌های بارگذاری‌شده<input value={search} onChange={(e) => setSearch(e.target.value)} type="search" /></label>
    {busy && <p role="status">در حال دریافت یا ذخیره…</p>}
    {error && <p role="alert">{error}</p>}
    {!busy && !items.length && !error && <p>هنوز گفت‌وگویی ندارید. از یک نیاز خرید شروع کنید.</p>}
    {items.length > 0 && !items.some((i) => i.title.includes(search)) && <p>در عنوان‌های بارگذاری‌شده نتیجه‌ای پیدا نشد.</p>}
    <ul>{items.filter((i) => i.title.includes(search)).map((item) => <li key={item.id}>
      <button className="history-open" disabled={busy} onClick={async () => { setBusy(true); try { await open(item.id); close() } catch { setError('گفت‌وگو در دسترس نیست یا منقضی شده است.') } finally { setBusy(false) } }}>
        <bdi>{item.title}</bdi><time dateTime={item.updated_at}>{new Date(item.updated_at).toLocaleDateString('fa-IR')}</time>
      </button><button aria-label={`حذف ${item.title}`} disabled={busy} onClick={() => setConfirm(item.id)}>حذف</button>
    </li>)}</ul>
    {cursor && <button disabled={busy} onClick={async () => { setBusy(true); try { const next = await copilotApi.list(cursor); setItems((old) => [...old, ...next.items]); setCursor(next.next_cursor) } catch { setError('بارگذاری بیشتر انجام نشد.') } finally { setBusy(false) } }}>بارگذاری بیشتر</button>}
    {items.length > 0 && <button className="danger-link" disabled={busy} onClick={() => setConfirm('all')}>پاک‌کردن همهٔ گفت‌وگوها</button>}
    {confirm && <section className="delete-confirm" role="alert" aria-label="تأیید حذف">
      <p>{confirm === 'all' ? 'همهٔ گفت‌وگوها حذف شوند؟' : 'این گفت‌وگو حذف شود؟'} بازگردانی ندارد.</p>
      <p>حافظهٔ مشتق‌شده از گفت‌وگو هم حذف می‌شود؛ کلیدها و تنظیمات مستقل باقی می‌مانند. حذف نسخهٔ پشتیبان فوری نیست.</p>
      <button disabled={busy} onClick={() => void remove()}>بله، حذف شود</button><button disabled={busy} onClick={() => setConfirm(null)}>انصراف</button>
    </section>}
  </dialog>
}
