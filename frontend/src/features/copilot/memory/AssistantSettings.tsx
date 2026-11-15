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
    void Promise.all([memoryApi.credential(), memoryApi.settings()]).then(([c, s]) => { if (active) { setCredential(c); setSettings(s) } }).catch(e => { if (active) setError(failureText(e)) })
    return () => { active = false }
  }, [])
  const save = async (event: FormEvent) => {
    event.preventDefault(); if (!credential) return
    setBusy(true); setError(''); const submitted = key; setKey('')
    try { setCredential(await memoryApi.saveKey(submitted, credential.revision)) }
    catch (reason) { setError(failureText(reason)) }
    finally { setBusy(false) }
  }
  const remove = async () => {
    if (!credential) return
    setBusy(true); setError(''); setKey('')
    try { await memoryApi.deleteKey(credential.revision); setCredential(await memoryApi.credential()) }
    catch (reason) { setError(failureText(reason)) }
    finally { setBusy(false) }
  }
  return <section className="personal-panel" aria-labelledby="assistant-settings-title">
    <h1 id="assistant-settings-title">تنظیمات دستیار</h1>
    <p className="readiness-notice">اتصال زنده مسدود است: کاربران و سرور ایران در منطقهٔ پشتیبانی‌شدهٔ OpenAI نیستند. ذخیرهٔ کلید این محدودیت را رفع نمی‌کند.</p>
    <h2>کلید شخصی OpenAI</h2><p>اشتراک ChatGPT و هزینهٔ API جدا هستند. ذخیره‌کردن کلید هیچ درخواست یا هزینه‌ای ایجاد نمی‌کند.</p>
    {credential && <><p role="status">{states[credential.state] ?? 'وضعیت نامشخص'}</p>
      {credential.masked && <p>کلید ذخیره‌شده: <bdi>{credential.masked}</bdi></p>}
      {!credential.encryption_available && <p>ذخیره فعلاً در دسترس نیست؛ فایل کلید رمزنگاری باید روی سرور محلی تنظیم شود.</p>}
      <form onSubmit={save} autoComplete="off"><label>کلید OpenAI<input type="password" value={key} onChange={e => setKey(e.target.value)} autoComplete="new-password" spellCheck={false} maxLength={512} dir="ltr" /></label>
        <div className="personal-actions"><button className="button primary" disabled={busy || !key || !credential.encryption_available}>{credential.masked ? 'جایگزینی کلید' : 'ذخیرهٔ کلید'}</button>
        {credential.masked && <button type="button" className="button ghost" disabled={busy} onClick={() => void remove()}>حذف کلید</button>}</div></form>
      {credential.expires_at && <p>پایان نگه‌داری: {new Date(credential.expires_at).toLocaleDateString('fa-IR')}</p>}
    </>}
    <h2>مدل و وضعیت اتصال</h2>
    <p>فهرست زیر از مستندات رسمی است؛ دسترسی حساب شما بررسی نشده و اعتبارسنجی آنلاین در این مرحله غیرفعال است.</p>
    {settings && <label>مدل مستندشده<select value={settings.model} disabled={busy} onChange={async e => {
      setBusy(true); setError('')
      try { setSettings(await memoryApi.update({ expected_revision: settings.revision, model: e.target.value })) }
      catch (reason) { setError(failureText(reason)) } finally { setBusy(false) }
    }}>{settings.catalog.saved_status === 'UNAVAILABLE' && <option value={settings.model}>مدل ذخیره‌شده دیگر در فهرست نیست</option>}
      {settings.catalog.items.map(m => <option key={m.id} value={m.id}>{m.id} — تأییدنشده برای حساب</option>)}</select></label>}
    <p>اگر مدل در دسترس نباشد، درخواست متوقف می‌شود؛ مدل یا ارائه‌دهندهٔ دیگری خودکار جایگزین نمی‌شود.</p>
    <details><summary>حریم خصوصی و محدودیت حذف</summary><p>کلید فقط رمز‌شده در سرور نگه‌داری می‌شود و دوباره نمایش داده نمی‌شود. سیاست موقت توسعه ۳۰ روز است، محدود به عمر دسترسی شما؛ فقط همین مرورگر دسترسی دارد. گم‌شدن دسترسی مرورگر بازیابی خودکار ندارد. حذف یا جایگزینی، کارهای صف‌شده را باطل می‌کند؛ درخواست قبلاً ارسال‌شده قابل پس‌گرفتن نیست. حذف فوری از نسخه‌های پشتیبان تضمین نمی‌شود.</p></details>
    {error && <p role="alert">{error}</p>}
  </section>
}
