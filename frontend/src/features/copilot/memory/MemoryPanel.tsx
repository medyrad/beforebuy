import { useEffect, useState } from 'react'
import { memoryApi, failureText } from './api'
import type { Memory, Settings } from './api'
import { preferenceLabel } from './labels'

export function MemoryPanel() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [items, setItems] = useState<Memory[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [clear, setClear] = useState(false)
  const reload = async () => { const [s, list] = await Promise.all([memoryApi.settings(), memoryApi.list()]); setSettings(s); setItems(list.items) }
  useEffect(() => { let active = true; void Promise.all([memoryApi.settings(), memoryApi.list()]).then(([s, list]) => { if (active) { setSettings(s); setItems(list.items) } }).catch(e => { if (active) setError(failureText(e)) }); return () => { active = false } }, [])
  const action = async (work: () => Promise<unknown>) => {
    setBusy(true); setError('')
    try { await work(); await reload() } catch (reason) { setError(failureText(reason)) } finally { setBusy(false) }
  }
  return <section className="personal-panel" aria-labelledby="memory-title"><h1 id="memory-title">شناخت من</h1>
    <p>فقط ترجیح‌هایی که خودتان تأیید می‌کنید برای خرید بعدی پیشنهاد می‌شوند. هدیه و خانه از ترجیح شخصی شما جدا هستند.</p>
    {settings && <><p role="status">حافظه {settings.memory_enabled ? 'روشن' : 'خاموش'} است.</p><button className="button primary" disabled={busy} onClick={() => void action(() => memoryApi.update({ expected_revision: settings.revision, memory_enabled: !settings.memory_enabled }))}>{settings.memory_enabled ? 'خاموش‌کردن حافظه' : 'فعال‌کردن حافظه با رضایت من'}</button></>}
    <p>پیشنهادها فقط از معیارهای ساختاریافتهٔ نیاز تأییدشده می‌آیند؛ یادگیری آزاد از متن یا ویژگی‌های حساس انجام نمی‌شود.</p>
    {items.length === 0 && <p>هنوز ترجیحی ذخیره نشده. در میز خرید، نیاز را تأیید و «پیشنهاد ترجیح برای شناخت من» را انتخاب کنید.</p>}
    <div className="memory-list">{items.map(item => <MemoryItem key={`${item.id}:${item.revision}`} item={item} busy={busy || !settings?.memory_enabled} onEdit={data => action(() => memoryApi.edit(item.id, { expected_revision: item.revision, ...data }))} onDelete={() => action(() => memoryApi.remove(item.id))} />)}</div>
    <div className="personal-actions"><a href="/api/v1/copilot/memory/export" download="beforebuy-preferences.json">دریافت نسخهٔ ترجیح‌های من</a><button className="text-button" disabled={busy || !items.length} onClick={() => setClear(true)}>پاک‌کردن همهٔ ترجیح‌ها</button></div>
    {clear && <div className="readiness-notice"><p>همهٔ ترجیح‌ها از فضای فعال حذف شوند؟</p><button className="button ghost" disabled={busy} onClick={() => void action(async () => { await memoryApi.remove(); setClear(false) })}>بله، همه را حذف کن</button><button className="text-button" onClick={() => setClear(false)}>انصراف</button></div>}
    <details><summary>نگه‌داری و گفت‌وگوی بدون حافظه</summary><p>سیاست موقت توسعه: پیشنهاد ۷ روز، تأییدشده ۹۰ روز، محدود به عمر گفت‌وگوی مبدأ و دسترسی مرورگر. خواندن یا ویرایش این مدت را تمدید نمی‌کند. خاموش‌کردن، استفاده و پیشنهاد تازه را متوقف می‌کند؛ حذف جداست. حذف گفت‌وگوی مبدأ ترجیح‌های مشتق‌شده را هم حذف می‌کند. «گفت‌وگوی بدون حافظه» چیزی از ترجیح‌های ذخیره‌شده نمی‌خواند و به آن‌ها اضافه نمی‌کند؛ خود گفت‌وگو همچنان طبق سیاست معمول نگه‌داری می‌شود. حذف فوری از backup تضمین نمی‌شود و بازیابی بین مرورگرها نداریم.</p></details>
    {error && <p role="alert">{error}</p>}
  </section>
}

function MemoryItem({ item, busy, onEdit, onDelete }: { item: Memory; busy: boolean; onEdit: (data: Record<string, unknown>) => Promise<void>; onDelete: () => Promise<void> }) {
  const [edit, setEdit] = useState(false)
  const [value, setValue] = useState(String(item.criterion.expected))
  return <article className="memory-item"><h2>{preferenceLabel(item)}</h2><p>{item.state === 'CONFIRMED' ? 'تأییدشده برای پیشنهاد در خرید بعدی' : item.state === 'REJECTED' ? 'ردشده؛ استفاده نمی‌شود' : 'پیشنهاد؛ منتظر تأیید'}</p>
    <p>پایان نگه‌داری: {new Date(item.expires_at).toLocaleDateString('fa-IR')}</p>
    <div className="personal-actions">{item.state === 'CANDIDATE' && <><button className="button primary" disabled={busy} onClick={() => void onEdit({ state: 'CONFIRMED' })}>تأیید ترجیح</button><button className="button ghost" disabled={busy} onClick={() => void onEdit({ state: 'REJECTED' })}>رد پیشنهاد</button></>}
      <button className="text-button" disabled={busy} onClick={() => setEdit(!edit)}>اصلاح ترجیح</button><button className="text-button" onClick={() => void onDelete()}>حذف ترجیح</button></div>
    {edit && <form onSubmit={e => { e.preventDefault(); void onEdit({ criterion: { ...item.criterion, expected: typeof item.criterion.expected === 'boolean' ? value === 'true' : Number(value) } }).then(() => setEdit(false)) }}>
      <label>مقدار اصلاح‌شده{typeof item.criterion.expected === 'boolean' ? <select value={value} onChange={e => setValue(e.target.value)}><option value="true">بله</option><option value="false">خیر</option></select> : <input type="number" min="1" max="100000" required value={value} onChange={e => setValue(e.target.value)} />}</label><button className="button primary" disabled={busy}>ذخیرهٔ اصلاح</button></form>}
  </article>
}
