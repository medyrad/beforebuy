import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { memoryApi, failureText } from './api'
import type { Credential, Settings } from './api'
const states: Record<string, string> = { NOT_CONFIGURED: 'کلیدی ذخیره نشده', STORED_UNVALIDATED: 'ذخیره‌شده؛ اعتبارسنجی نشده',
  VALIDATION_FAILED: 'اعتبارسنجی ناموفق', VALIDATION_BLOCKED: 'اعتبارسنجی در دسترس نیست', VALIDATED: 'اعتبارسنجی‌شده' }

export function AssistantSettings() {
  const [credential, setCredential] = useState<Credential | null>(null)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [key, setKey] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    void memoryApi.settings().then(async s => ({ s, c: await memoryApi.credential(s.provider) }))
      .then(({ c, s }) => { if (active) { setCredential(c); setSettings(s) } })
      .catch(e => { if (active) setError(failureText(e)) })
    return () => { active = false }
  }, [])
  const save = async (event: FormEvent) => {
    event.preventDefault(); if (!credential) return
    setBusy(true); setError(''); const submitted = key; setKey('')
    try { setCredential(await memoryApi.saveKey(credential.provider, submitted, credential.revision)) }
    catch (reason) { setError(failureText(reason)) }
    finally { setBusy(false) }
  }
  const remove = async () => {
    if (!credential) return
    setBusy(true); setError(''); setKey('')
    try { await memoryApi.deleteKey(credential.provider, credential.revision); setCredential(await memoryApi.credential(credential.provider)) }
    catch (reason) { setError(failureText(reason)) }
    finally { setBusy(false) }
  }
  return <section className="personal-panel" aria-labelledby="assistant-settings-title">
    <h1 id="assistant-settings-title">تنظیمات دستیار</h1>
    <p className="readiness-notice">مسیر منتخب GapGPT با مدل میزبانی‌شده در ایران آمادهٔ پیکربندی است؛ اتصال زنده تا ثبت جداگانهٔ اعتبارنامه، اعتبارسنجی و مجوز هزینه خاموش می‌ماند.</p>
    {settings && <label>ارائه‌دهنده<select value={settings.provider} disabled={busy} onChange={async e => {
      setBusy(true); setError(''); setKey('')
      try {
        const next = await memoryApi.update({ expected_revision: settings.revision, provider: e.target.value })
        setSettings(next); setCredential(await memoryApi.credential(next.provider))
      } catch (reason) { setError(failureText(reason)) } finally { setBusy(false) }
    }}><option value="gapgpt">GapGPT — مسیر منتخب ایران</option><option value="openai">OpenAI قدیمی — غیرفعال در ایران</option></select></label>}
    <h2>کلید {settings?.provider === 'openai' ? 'OpenAI' : 'GapGPT'}</h2>
    <p>کلید هر ارائه‌دهنده جدا و رمز‌شده نگه‌داری می‌شود. ذخیره‌کردن آن هیچ درخواست یا هزینه‌ای ایجاد نمی‌کند و کلید OpenAI قدیمی حذف یا جایگزین نمی‌شود.</p>
    {credential && <><p role="status">{states[credential.state] ?? 'وضعیت نامشخص'}</p>
      {credential.masked && <p>کلید ذخیره‌شده: <bdi>{credential.masked}</bdi></p>}
      {!credential.encryption_available && <p>ذخیره فعلاً در دسترس نیست؛ فایل کلید رمزنگاری باید روی سرور محلی تنظیم شود.</p>}
      <form onSubmit={save} autoComplete="off"><label>کلید {settings?.provider === 'openai' ? 'OpenAI' : 'GapGPT'}<input type="password" value={key} onChange={e => setKey(e.target.value)} autoComplete="new-password" spellCheck={false} maxLength={512} dir="ltr" /></label>
        <div className="personal-actions"><button className="button primary" disabled={busy || !key || !credential.encryption_available}>{credential.masked ? 'جایگزینی کلید' : 'ذخیرهٔ کلید'}</button>
        {credential.masked && <button type="button" className="button ghost" disabled={busy} onClick={() => void remove()}>حذف کلید</button>}</div></form>
      {credential.expires_at && <p>پایان نگه‌داری: {new Date(credential.expires_at).toLocaleDateString('fa-IR')}</p>}
    </>}
    <h2>مدل و وضعیت اتصال</h2>
    <p>فهرست زیر از مستندات رسمی است؛ دسترسی حساب بررسی نشده و هیچ fallback خودکاری میان ارائه‌دهنده‌ها وجود ندارد.</p>
    {settings && <label>مدل مستندشده<select value={settings.model} disabled={busy} onChange={async e => {
      setBusy(true); setError('')
      try { setSettings(await memoryApi.update({ expected_revision: settings.revision, model: e.target.value })) }
      catch (reason) { setError(failureText(reason)) } finally { setBusy(false) }
    }}>{settings.catalog.saved_status === 'UNAVAILABLE' && <option value={settings.model}>مدل ذخیره‌شده دیگر در فهرست نیست</option>}
      {settings.catalog.items.map(m => <option key={m.id} value={m.id}>{m.id} — تأییدنشده برای حساب</option>)}</select></label>}
    <button className="button ghost" type="button" disabled={busy} onClick={async () => {
      setBusy(true); setError('')
      try {
        const catalog = await memoryApi.refreshModels()
        setSettings(current => current ? { ...current, catalog } : current)
      } catch (reason) { setError(failureText(reason)) } finally { setBusy(false) }
    }}>بررسی صریح مدل‌های حساب</button>
    <p>این بررسی فقط با اقدام شما انجام می‌شود. GapGPT endpoint بدون‌هزینه‌ای برای اعتبارسنجی مستند نکرده، بنابراین بدون مجوز هزینه fail-closed می‌شود؛ خواندن یا ذخیرهٔ تنظیمات هیچ درخواست شبکه‌ای به ارائه‌دهنده نمی‌فرستد.</p>
    <p>اگر مدل در دسترس نباشد، درخواست متوقف می‌شود؛ مدل یا ارائه‌دهندهٔ دیگری خودکار جایگزین نمی‌شود.</p>
    <details><summary>حریم خصوصی و محدودیت حذف</summary><p>کلید فقط رمز‌شده در سرور نگه‌داری می‌شود و دوباره نمایش داده نمی‌شود. سیاست موقت توسعه ۳۰ روز است، محدود به عمر دسترسی شما؛ فقط همین مرورگر دسترسی دارد. گم‌شدن دسترسی مرورگر بازیابی خودکار ندارد. حذف یا جایگزینی، کارهای صف‌شده را باطل می‌کند؛ درخواست قبلاً ارسال‌شده قابل پس‌گرفتن نیست. حذف فوری از نسخه‌های پشتیبان تضمین نمی‌شود.</p></details>
    {error && <p role="alert">{error}</p>}
  </section>
}
