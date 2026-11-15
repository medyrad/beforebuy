import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { memoryApi, failureText } from './api'
import type { Credential, Settings } from './api'
const states: Record<string, string> = { NOT_CONFIGURED: 'کلیدی ذخیره نشده', STORED_UNVALIDATED: 'ذخیره‌شده؛ اعتبارسنجی نشده',
  VALIDATION_FAILED: 'اعتبارسنجی ناموفق', VALIDATION_BLOCKED: 'اعتبارسنجی در دسترس نیست', VALIDATED: 'اعتبارسنجی‌شده' }

export function AssistantSettings() {
  const [credential, setCredential] = useState<Credential | null>(null)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [key, setKey] = useState('')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [notice, setNotice] = useState('')
  const locked = useRef(true)
  const generation = useRef(0)
  // The ref closes the same-render double-submit window; generation invalidates
  // every asynchronous continuation when this settings view is left or reloaded.
  const run = async (work: (current: () => boolean) => Promise<void>) => {
    if (locked.current) return
    locked.current = true
    const token = generation.current
    const current = () => generation.current === token
    setBusy(true); setError(''); setNotice('')
    try { await work(current) }
    catch (reason) { if (current()) setError(failureText(reason)) }
    finally { if (current()) { locked.current = false; setBusy(false) } }
  }
  useEffect(() => {
    let active = true
    locked.current = true
    void memoryApi.settings().then(async s => {
      if (!active) return
      const c = await memoryApi.credential(s.provider)
      if (active) { setCredential(c); setSettings(s) }
    })
      .catch(e => { if (active) setError(failureText(e)) })
      .finally(() => { if (active) { locked.current = false; setBusy(false) } })
    return () => { active = false; generation.current += 1; locked.current = true }
  }, [reload])
  const save = async (event: FormEvent) => {
    event.preventDefault(); if (busy || !credential || credential.provider !== settings?.provider) return
    await run(async current => {
      const submitted = key; setKey('')
      const next = await memoryApi.saveKey(credential.provider, submitted, credential.revision)
      if (current()) { setCredential(next); setNotice('کلید ذخیره شد؛ اتصال زنده فعال نشده است.') }
    })
  }
  const remove = async () => {
    if (busy || !credential || credential.provider !== settings?.provider) return
    await run(async current => {
      setKey(''); setCredential(null)
      await memoryApi.deleteKey(credential.provider, credential.revision)
      if (!current()) return
      const next = await memoryApi.credential(credential.provider)
      if (current()) setCredential(next)
    })
  }
  return <section className="personal-panel" aria-labelledby="assistant-settings-title">
    <h1 id="assistant-settings-title">تنظیمات دستیار</h1>
    <p className="readiness-notice">{settings?.provider === 'openai' ? 'ذخیرهٔ کلید OpenAI از فعال‌سازی جداست؛ اتصال مستقیم برای استقرار ایران غیرفعال می‌ماند.' : 'مسیر منتخب GapGPT با مدل میزبانی‌شده در ایران آمادهٔ پیکربندی است؛ اتصال زنده تا ثبت جداگانهٔ اعتبارنامه، اعتبارسنجی و مجوز هزینه خاموش می‌ماند.'}</p>
    {settings && <label>ارائه‌دهنده<select value={settings.provider} disabled={busy} onChange={e => {
      const provider = e.target.value
      void run(async current => {
        setKey(''); setCredential(null)
        const next = await memoryApi.update({ expected_revision: settings.revision, provider })
        if (!current()) return
        setSettings(next)
        const loaded = await memoryApi.credential(next.provider)
        if (current()) setCredential(loaded)
      })
    }}><option value="gapgpt">GapGPT — مسیر منتخب ایران</option><option value="openai">OpenAI قدیمی — غیرفعال در ایران</option></select></label>}
    <h2>کلید {settings?.provider === 'openai' ? 'OpenAI' : 'GapGPT'}</h2>
    <p>کلید هر ارائه‌دهنده جدا و رمز‌شده نگه‌داری می‌شود. ذخیره‌کردن آن هیچ درخواست یا هزینه‌ای ایجاد نمی‌کند و کلید OpenAI قدیمی حذف یا جایگزین نمی‌شود.</p>
    {credential && credential.provider === settings?.provider && <><p role="status">{states[credential.state] ?? 'وضعیت نامشخص'}</p>
      {credential.masked && <p>کلید ذخیره‌شده: <bdi>{credential.masked}</bdi></p>}
      {!credential.encryption_available && <p>ذخیره فعلاً در دسترس نیست؛ فایل کلید رمزنگاری باید روی سرور محلی تنظیم شود.</p>}
      <form onSubmit={save} autoComplete="off"><label>کلید {settings?.provider === 'openai' ? 'OpenAI' : 'GapGPT'}<input type="password" value={key} onChange={e => setKey(e.target.value)} autoComplete="new-password" spellCheck={false} maxLength={512} dir="ltr" /></label>
        <div className="personal-actions"><button className="button primary" disabled={busy || !key || !credential.encryption_available}>{credential.masked ? 'جایگزینی کلید' : 'ذخیرهٔ کلید'}</button>
        {credential.masked && <button type="button" className="button ghost" disabled={busy} onClick={() => void remove()}>حذف کلید</button>}</div></form>
      {credential.expires_at && <p>پایان نگه‌داری: {new Date(credential.expires_at).toLocaleDateString('fa-IR')}</p>}
    </>}
    <h2>مدل و وضعیت اتصال</h2>
    <p>فهرست زیر از مستندات رسمی است؛ دسترسی حساب بررسی نشده و هیچ fallback خودکاری میان ارائه‌دهنده‌ها وجود ندارد.</p>
    {settings && <label>مدل مستندشده<select value={settings.model} disabled={busy} onChange={e => {
      const model = e.target.value
      void run(async current => {
        setKey(''); setCredential(null)
        const next = await memoryApi.update({ expected_revision: settings.revision, model })
        if (!current()) return
        setSettings(next)
        const loaded = await memoryApi.credential(next.provider)
        if (current()) setCredential(loaded)
      })
    }}>{settings.catalog.saved_status === 'UNAVAILABLE' && <option value={settings.model}>مدل ذخیره‌شده دیگر در فهرست نیست</option>}
      {settings.catalog.items.map(m => <option key={m.id} value={m.id}>{'\u2066'}{m.id}{'\u2069'} — تأییدنشده برای حساب</option>)}</select></label>}
    {settings && <p className="selected-model-label">شناسهٔ مدل انتخاب‌شده: <bdi>{settings.model}</bdi></p>}
    <button className="button ghost" type="button" disabled={busy || !settings} onClick={() => void run(async current => {
        const catalog = await memoryApi.refreshModels()
        if (current()) setSettings(value => value ? { ...value, catalog } : value)
    })}>بررسی صریح مدل‌های حساب</button>
    <p>این بررسی فقط با اقدام شما انجام می‌شود. GapGPT endpoint بدون‌هزینه‌ای برای اعتبارسنجی مستند نکرده، بنابراین بدون مجوز هزینه fail-closed می‌شود؛ خواندن یا ذخیرهٔ تنظیمات هیچ درخواست شبکه‌ای به ارائه‌دهنده نمی‌فرستد.</p>
    <p>اگر مدل در دسترس نباشد، درخواست متوقف می‌شود؛ مدل یا ارائه‌دهندهٔ دیگری خودکار جایگزین نمی‌شود.</p>
    <details><summary>سهمیهٔ رایگان API — در حال بررسی</summary>
      <p>OpenRouter مدل‌های دارای سهمیهٔ رایگان دارد؛ سهمیه محدود است و رایگان‌بودن، دسترسی مجاز از ایران یا محرمانگی همهٔ مدل‌ها را تضمین نمی‌کند.</p>
      <p>اتصال OpenRouter هنوز پیاده‌سازی و تأیید نشده است؛ فعلاً کلید آن را در کادر OpenAI یا GapGPT وارد نکنید. ابتدا شرایط ارائهٔ خدمت به کاربران و سرور ایران و سیاست دادهٔ مدل منتخب باید روشن شود.</p>
      <a href="https://openrouter.ai/settings/keys" target="_blank" rel="noopener noreferrer">ساخت حساب و کلید در OpenRouter</a>{' · '}
      <a href="https://openrouter.ai/collections/free-models" target="_blank" rel="noopener noreferrer">مدل‌ها و محدودیت‌های رایگان</a>
      <p>ورود در سایت خود سرویس انجام می‌شود؛ رمز حساب یا کلید را در گفتگو نفرستید. ساخت حساب به‌تنهایی اتصال این برنامه را فعال نمی‌کند.</p>
    </details>
    <details><summary>حریم خصوصی و محدودیت حذف</summary><p>کلید فقط رمز‌شده در سرور نگه‌داری می‌شود و دوباره نمایش داده نمی‌شود. سیاست موقت توسعه ۳۰ روز است، محدود به عمر دسترسی شما؛ فقط همین مرورگر دسترسی دارد. گم‌شدن دسترسی مرورگر بازیابی خودکار ندارد. حذف یا جایگزینی، کارهای صف‌شده را باطل می‌کند؛ درخواست قبلاً ارسال‌شده قابل پس‌گرفتن نیست. حذف فوری از نسخه‌های پشتیبان تضمین نمی‌شود.</p></details>
    {notice && <p role="status">{notice}</p>}
    {error && <><p role="alert">{error}</p><button type="button" className="button ghost" disabled={busy} onClick={() => {
      if (locked.current) return
      locked.current = true; generation.current += 1
      setBusy(true); setError(''); setNotice(''); setKey(''); setCredential(null); setSettings(null); setReload(value => value + 1)
    }}>بارگذاری دوبارهٔ تنظیمات</button></>}
  </section>
}
