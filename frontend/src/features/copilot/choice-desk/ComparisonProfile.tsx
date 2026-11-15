import type { Brief } from '../conversation/types'
import { labels } from './labels'

type Profile = NonNullable<Brief['comparison']>
const categoryFields: Record<string, string[]> = { electronics: ['capacity_gb', 'portable'], home: ['capacity_l', 'dishwasher_safe'], sports: ['size_eu', 'waterproof'] }
const numeric = new Set(['capacity_gb', 'capacity_l', 'size_eu'])

export function ComparisonProfile({ value, onChange, category, recipient }: { value: Profile; onChange: (value: Profile) => void; category: string; recipient: string }) {
  const criteria = value.criteria ?? []
  const fields = categoryFields[category] ?? []
  const scope = recipient === 'GIFT' ? 'RECIPIENT' : recipient === 'HOUSEHOLD' ? 'HOUSEHOLD' : 'SELF'
  return <fieldset className="comparison-profile"><legend>ترجیحات مقایسه — اختیاری</legend>
    <label>هدف خرید<select value={value.intent ?? 'UNKNOWN'} onChange={(e) => onChange({ ...value, intent: e.target.value })}><option value="UNKNOWN">هنوز نمی‌دانم</option><option value="PRACTICAL">جایگزینی کاربردی</option><option value="ENJOYMENT">لذت یا پاداش به خودم</option><option value="GIFT">هدیه</option><option value="HOUSEHOLD">خرید برای خانه</option></select></label>
    <label>نوع سقف بودجه<select value={value.budget_mode ?? 'STRICT'} onChange={(e) => onChange({ ...value, budget_mode: e.target.value })}><option value="STRICT">قطعی؛ بالاتر از سقف مناسب نیست</option><option value="FLEXIBLE">با تأیید من انعطاف‌پذیر است</option></select></label>
    <label>ترجیح هزینه<select value={value.prefer_lower_cost ? 'yes' : 'no'} onChange={(e) => onChange({ ...value, prefer_lower_cost: e.target.value === 'yes' })}><option value="no">ارزان‌تر بودن اولویت جداگانه نیست</option><option value="yes">در شرایط برابر هزینهٔ نهایی کمتر</option></select></label>
    <p>فقط معیار صریح شما بررسی می‌شود. معیار هدیه متعلق به گیرنده است، نه خریدار. شرط عددی یعنی مقدار دقیق، نه حداقل.</p>
    {fields.map((field) => {
      const criterion = criteria.find((c) => c.field === field && c.scope === scope)
      const update = (change: Partial<NonNullable<Profile['criteria']>[number]> | null) => onChange({ ...value, criteria: [
        ...criteria.filter((c) => c.field !== field), ...(change ? [{ field, expected: numeric.has(field) ? 1 : true, kind: 'HARD', scope, ...criterion, ...change }] : []),
      ] })
      return <div key={field}><label>{labels[field]}<select value={criterion?.kind ?? ''} onChange={(e) => update(e.target.value ? { kind: e.target.value } : null)}><option value="">هنوز مشخص نیست / معیار نیست</option><option value="HARD">شرط قطعی</option><option value="PREFERENCE">ترجیح</option></select></label>
        {criterion && (numeric.has(field) ? <label>مقدار دقیق {labels[field]}<input type="number" min="1" max="100000" required value={Number(criterion.expected)} onChange={(e) => update({ expected: Number(e.target.value) })} /></label> : <label>انتظار شما: {labels[field]}<select value={criterion.expected ? 'yes' : 'no'} onChange={(e) => update({ expected: e.target.value === 'yes' })}><option value="yes">بله</option><option value="no">خیر</option></select></label>)}</div>
    })}
    {!fields.length && <p>برای معیارهای نمونه، دسته را electronics، home یا sports وارد کنید؛ دسته‌های دیگر فقط بودجه و شواهد موجود را مقایسه می‌کنند.</p>}
    {criteria.some((c) => !fields.includes(c.field) || c.scope !== scope) && <p>معیارهایی از دسته یا مخاطب قبلی باقی مانده‌اند. <button type="button" className="text-button" onClick={() => onChange({ ...value, criteria: criteria.filter((c) => fields.includes(c.field) && c.scope === scope) })}>حذف معیارهای نامرتبط</button></p>}
  </fieldset>
}
