import { useEffect, useRef, useState } from 'react'

import type { AnalysisInput } from '../../services/api/types'
import { q001, q002, q003, q004, q006 } from './options'
import { buildSubmission, deriveFollowUps, type Draft, validateMoney } from './draft'

interface Props {
  initialDraft: Draft
  onSubmit: (input: AnalysisInput) => void | Promise<void>
  onCancel: () => void
  submitting?: boolean
  serverErrors?: Record<string, string[]>
}

type Errors = Record<string, string>

function RadioGroup({ legend, name, value, options, onChange }: {
  legend: string; name: string; value: string; options: ReadonlyArray<readonly [string, string]>; onChange: (value: string) => void
}) {
  return <fieldset className="choice-group">
    <legend>{legend}</legend>
    <div className="choice-grid">
      {options.map(([key, label]) => <label className="choice" key={key}>
        <input type="radio" name={name} value={key} checked={value === key} onChange={() => onChange(key)} />
        <span>{label}</span>
      </label>)}
    </div>
  </fieldset>
}

function CheckGroup({ legend, values, options, maximum, exclusive, onChange }: {
  legend: string; values: string[]; options: ReadonlyArray<readonly [string, string]>; maximum?: number; exclusive: string[]; onChange: (value: string[]) => void
}) {
  const toggle = (key: string) => {
    if (values.includes(key)) return onChange(values.filter((item) => item !== key))
    if (exclusive.includes(key)) return onChange([key])
    const next = values.filter((item) => !exclusive.includes(item))
    if (!maximum || next.length < maximum) onChange([...next, key])
  }
  return <fieldset className="choice-group">
    <legend>{legend}</legend>
    {maximum && <p className="field-hint">حداکثر {maximum.toLocaleString('fa-IR')} گزینه</p>}
    <div className="choice-grid">
      {options.map(([key, label]) => <label className="choice" key={key}>
        <input type="checkbox" checked={values.includes(key)} onChange={() => toggle(key)} />
        <span>{label}</span>
      </label>)}
    </div>
  </fieldset>
}

export function Questionnaire({ initialDraft, onSubmit, onCancel, submitting = false, serverErrors = {} }: Props) {
  const [draft, setDraft] = useState<Draft>(() => ({ ...initialDraft }))
  const [step, setStep] = useState(0)
  const [errors, setErrors] = useState<Errors>({})
  const formRef = useRef<HTMLFormElement>(null)
  const followUps = deriveFollowUps(draft)
  const totalSteps = followUps.length ? 4 : 3
  const serverError = Object.values(serverErrors).flat()[0]

  useEffect(() => {
    if (!Object.keys(errors).length) return
    const invalid = formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"], .field-error')
    invalid?.focus()
  }, [errors])

  const update = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }))
    setErrors({})
  }

  const validateStep = (): Errors => {
    const next: Errors = {}
    if (step === 0) {
      if (draft.productLabel.trim().length < 2) next.productLabel = 'نام یا توضیح مدل باید دست‌کم دو نویسه باشد.'
      const priceError = validateMoney(draft.price, false)
      if (priceError) next.price = priceError
    }
    if (step === 1) {
      if (!draft.q001) next.q001 = 'وضعیت گوشی فعلی را انتخاب کنید.'
      if (!draft.q002) next.q002 = 'نتیجهٔ مورد انتظار را انتخاب کنید.'
      if (!draft.q003.length) next.q003 = 'دست‌کم یک کاربرد را انتخاب کنید.'
    }
    if (step === 2) {
      if (!draft.q004) next.q004 = 'زمان نیاز را انتخاب کنید.'
      if (!draft.q006.length) next.q006 = 'یک گزینه دربارهٔ راه‌های دیگر انتخاب کنید.'
      if (draft.budgetKind === 'amount') {
        const budgetError = validateMoney(draft.budget, true)
        if (budgetError) next.budget = budgetError
      }
    }
    if (step === 3 && followUps.includes('F-001') && draft.f001.length > 240) next.f001 = 'توضیح باید حداکثر ۲۴۰ نویسه باشد.'
    return next
  }

  const next = () => {
    const nextErrors = validateStep()
    if (Object.keys(nextErrors).length) { setErrors(nextErrors); return }
    if (step < totalSteps - 1) { setStep((current) => current + 1); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const nextErrors = validateStep()
    if (Object.keys(nextErrors).length) { setErrors(nextErrors); return }
    if (step < totalSteps - 1) { next(); return }
    void onSubmit(buildSubmission(draft))
  }

  const error = (key: string) => errors[key] ? <p id={`${key}-error`} className="field-error" tabIndex={-1} role="alert">{errors[key]}</p> : null

  return <section className="questionnaire" aria-labelledby="questionnaire-title">
    <div className="section-heading">
      <div>
        <p className="eyebrow">گام {Math.min(step + 1, totalSteps).toLocaleString('fa-IR')} از {totalSteps.toLocaleString('fa-IR')}</p>
        <h1 id="questionnaire-title">جزئیات تصمیم شما</h1>
      </div>
      <progress value={step + 1} max={totalSteps} aria-label="پیشرفت پرسش‌نامه" />
    </div>
    <form ref={formRef} onSubmit={submit} noValidate>
      {step === 0 && <div className="form-stack">
        <div className="field">
          <label htmlFor="product-label">چه تلفنی را برای خرید در نظر دارید؟</label>
          <input id="product-label" value={draft.productLabel} onChange={(event) => update('productLabel', event.target.value)} maxLength={120} aria-invalid={Boolean(errors.productLabel)} aria-describedby={errors.productLabel ? 'productLabel-error' : undefined} autoFocus />
          <p className="field-hint">نام مدل فقط برای عنوان گزارش است؛ مشخصات فنی از روی آن حدس زده نمی‌شود.</p>
          {error('productLabel')}
        </div>
        <div className="field">
          <label htmlFor="price">قیمت تقریبی این خرید چند تومان است؟</label>
          <div className="money-input"><input id="price" dir="ltr" inputMode="numeric" value={draft.price} onChange={(event) => update('price', event.target.value)} aria-invalid={Boolean(errors.price)} aria-describedby={errors.price ? 'price-error' : 'price-hint'} /><span>تومان</span></div>
          <p id="price-hint" className="field-hint">نمونه: ۱۲٬۵۰۰٬۰۰۰ — رقم فارسی یا لاتین پذیرفته می‌شود.</p>
          {error('price')}
        </div>
      </div>}

      {step === 1 && <div className="form-stack">
        <RadioGroup legend="وضعیت گوشی فعلی شما کدام است؟" name="q001" value={draft.q001} options={q001} onChange={(value) => update('q001', value)} />
        {error('q001')}
        <RadioGroup legend="مهم‌ترین نتیجه‌ای که از این خرید انتظار دارید چیست؟" name="q002" value={draft.q002} options={q002} onChange={(value) => update('q002', value)} />
        {error('q002')}
        <CheckGroup legend="این تلفن را بیشتر برای چه کارهایی می‌خواهید؟" values={draft.q003} options={q003} maximum={3} exclusive={['UNKNOWN']} onChange={(value) => update('q003', value)} />
        {error('q003')}
      </div>}

      {step === 2 && <div className="form-stack">
        <RadioGroup legend="چه زمانی به این خرید نیاز دارید؟" name="q004" value={draft.q004} options={q004} onChange={(value) => update('q004', value)} />
        {error('q004')}
        <fieldset className="choice-group">
          <legend>حداکثر بودجهٔ شما برای این خرید چند تومان است؟</legend>
          <div className="budget-row">
            <label className="choice"><input type="radio" name="budgetKind" checked={draft.budgetKind === 'amount'} onChange={() => update('budgetKind', 'amount')} /><span>مبلغ مشخص</span></label>
            <label className="choice"><input type="radio" name="budgetKind" checked={draft.budgetKind === 'zero'} onChange={() => update('budgetKind', 'zero')} /><span>صفر تومان</span></label>
            <label className="choice"><input type="radio" name="budgetKind" checked={draft.budgetKind === 'unknown'} onChange={() => update('budgetKind', 'unknown')} /><span>نمی‌دانم</span></label>
          </div>
          {draft.budgetKind === 'amount' && <div className="money-input compact"><input aria-label="مبلغ بودجه به تومان" dir="ltr" inputMode="numeric" value={draft.budget} onChange={(event) => update('budget', event.target.value)} aria-invalid={Boolean(errors.budget)} /><span>تومان</span></div>}
        </fieldset>
        {error('budget')}
        <CheckGroup legend="کدام گزینه‌ها یا محدودیت‌ها را واقعاً بررسی کرده‌اید؟" values={draft.q006} options={q006} exclusive={['NONE', 'UNKNOWN']} onChange={(value) => update('q006', value)} />
        {error('q006')}
      </div>}

      {step === 3 && <div className="form-stack">
        <div className="followup-intro"><p className="eyebrow">پرسش‌های روشن‌کننده</p><h2>فقط نکته‌های مؤثر</h2><p>بر اساس پاسخ‌ها {followUps.length.toLocaleString('fa-IR')} پرسش تکمیلی نمایش داده شده است؛ سقف کل سه پرسش است.</p></div>
        {followUps.includes('F-001') && <div className="field">
          <label htmlFor="f001">برای روشن‌شدن وضعیت، مشکل اصلی گوشی فعلی یا دلیل نبود گوشی را در یک جمله بگویید. <span className="optional">اختیاری</span></label>
          <textarea id="f001" maxLength={240} rows={3} value={draft.f001} onChange={(event) => update('f001', event.target.value)} aria-invalid={Boolean(errors.f001)} />
          <p className="field-hint">این توضیح به‌تنهایی تناقض پاسخ‌های اصلی را حل نمی‌کند.</p>{error('f001')}
        </div>}
        {followUps.includes('F-002') && <RadioGroup legend="کدام نتیجه به تصمیم فعلی شما نزدیک‌تر است؟" name="f002" value={draft.f002} options={[...q002.filter(([key]) => key !== 'UNKNOWN'), ['STILL_UNKNOWN', 'هنوز نمی‌دانم']]} onChange={(value) => update('f002', value)} />}
        {followUps.includes('F-003') && <RadioGroup legend="دربارهٔ مناسب‌بودن این مدل برای استفادهٔ ضروری‌تان چه اطلاعاتی دارید؟" name="f003" value={draft.f003} options={[
          ['USER_REPORTS_IT_FITS', 'بر اساس بررسی خودم مناسب است'], ['USER_REPORTS_IT_DOES_NOT_FIT', 'بر اساس بررسی خودم مناسب نیست'], ['NO_INFORMATION', 'اطلاعات کافی ندارم'],
        ]} onChange={(value) => update('f003', value)} />}
      </div>}

      {serverError && <p className="form-banner error" role="alert">{serverError}</p>}
      <div className="form-actions">
        <button type="button" className="button ghost" onClick={step === 0 ? onCancel : () => setStep((current) => current - 1)}>{step === 0 ? 'انصراف' : 'بازگشت'}</button>
        <button type="submit" className="button primary" disabled={submitting}>{submitting ? 'در حال ساخت تحلیل…' : step === totalSteps - 1 ? 'نمایش تحلیل' : 'ادامه'}</button>
      </div>
    </form>
  </section>
}
