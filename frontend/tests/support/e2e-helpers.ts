import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'

interface AnalysisOptions {
  product?: string
  price?: string
  state?: 'normal' | 'serious'
  budget?: 'amount' | 'zero' | 'unknown'
  followUps?: boolean
}

export async function completeAnalysis(page: Page, options: AnalysisOptions = {}) {
  const product = options.product ?? 'مدل نمونه X 256GB'
  await page.getByRole('button', { name: 'خریدم را بررسی کن' }).click()
  await page.getByRole('textbox', { name: /چه تلفنی/ }).fill(product)
  await page.getByRole('textbox', { name: /قیمت تقریبی.*تومان/ }).fill(options.price ?? '۱۲٬۵۰۰٬۰۰۰')
  await page.getByRole('button', { name: 'ادامه' }).click()

  if (options.state === 'serious') {
    await page.getByRole('radio', { name: 'مشکل جدی دارد' }).check()
  } else {
    await page.getByRole('radio', { name: 'گوشی فعلی قابل استفاده نیست' }).check()
  }
  const benefitGroup = page.getByRole('group', { name: 'مهم‌ترین نتیجه‌ای که از این خرید انتظار دارید چیست؟' })
  await benefitGroup.getByRole('radio', { name: options.followUps ? 'نمی‌دانم' : 'دسترسی ضروری را دوباره داشته باشم' }).check()
  if (options.followUps) {
    await page.getByRole('checkbox', { name: 'کار یا تحصیل' }).check()
    await page.getByRole('checkbox', { name: 'بازی' }).check()
    await page.getByRole('checkbox', { name: 'نیازهای دسترس‌پذیری' }).check()
  } else {
    await page.getByRole('checkbox', { name: 'استفادهٔ عمومی' }).check()
  }
  await page.getByRole('button', { name: 'ادامه' }).click()

  await page.getByRole('radio', { name: 'تا دو هفتهٔ آینده' }).check()
  if (options.budget === 'zero') {
    await page.getByRole('radio', { name: 'صفر تومان' }).check()
  } else if (options.budget === 'unknown') {
    await page.getByRole('group', { name: 'حداکثر بودجهٔ شما برای این خرید چند تومان است؟' }).getByRole('radio', { name: 'نمی‌دانم', exact: true }).check()
  } else {
    await page.getByRole('textbox', { name: 'مبلغ بودجه به تومان' }).fill('۱۵٬۰۰۰٬۰۰۰')
  }
  await page.getByRole('checkbox', { name: 'هیچ‌کدام' }).check()

  if (options.followUps) {
    await page.getByRole('button', { name: 'ادامه' }).click()
    await page.getByText(/۳ پرسش تکمیلی.*سقف کل سه پرسش/).waitFor()
    await page.getByLabel(/مشکل اصلی گوشی/).fill('باتری ناگهان خاموش می‌شود و تماس ضروری قطع می‌شود.')
    await page.getByRole('radio', { name: 'یک محدودیت مهم را حل کنم' }).check()
    await page.getByRole('radio', { name: 'اطلاعات کافی ندارم' }).check()
  }
  await page.getByRole('button', { name: 'نمایش تحلیل' }).click()
  await page.getByRole('heading', { name: /تعویض قابل توجیه|قیمت بالاتر از بودجه|اطلاعات بیشتری لازم/ }).waitFor()
}

export async function seriousAccessibilityViolations(page: Page) {
  const result = await new AxeBuilder({ page }).analyze()
  return result.violations.filter((item) => ['critical', 'serious'].includes(item.impact ?? ''))
}
