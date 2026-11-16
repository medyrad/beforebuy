import { resolve } from 'node:path'
import { mkdir } from 'node:fs/promises'
import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

// Synthetic user entries through real NGINX/API/PostgreSQL. No market/provider requests.
for (const width of [1440, 390]) {
  test(`manual unverified offers persist through NGINX at ${width}`, async ({ page }) => {
    // Local cold-start requests measured 15s; wait for state, never sleep or retry writes.
    test.setTimeout(180_000)
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')
    await page.getByRole('textbox', { name: 'پیام شما' }).fill('آزمون مصنوعی تلویزیون؛ بودجه‌ام ۲۰ میلیون تومان است')
    await page.getByRole('button', { name: 'ارسال پیام' }).click()
    await expect(page.locator('.message.assistant:not(.provisional)')).toHaveCount(1, { timeout: 30000 })
    if (width === 390) await page.getByRole('button', { name: 'میز انتخاب', exact: true }).click()
    await page.getByRole('button', { name: 'اصلاح نیاز خرید' }).click()
    await page.getByRole('combobox', { name: 'مخاطب', exact: true }).selectOption('SELF')
    await page.getByLabel('دسته', { exact: true }).fill('electronics')
    await page.getByLabel('سقف بودجه (تومان)').fill('20000000')
    await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
    await page.getByRole('button', { name: 'تأیید نیاز خرید' }).click()
    await page.getByText('ثبت پیشنهادی که خودم دیده‌ام', { exact: true }).click()
    for (const [label, value] of [['برند', 'SYNTHETIC'], ['نام دقیق محصول', 'تلویزیون آزمون، نه قیمت بازار'],
      ['کد مدل سازنده', 'SYNTHETIC-TV-55'], ['اندازهٔ نسخه', '55'], ['سال مدل', '2026']]) {
      await page.getByLabel(label, { exact: true }).fill(value)
    }
    const observed = new Date(Date.now() - 60000).toISOString().slice(0, 16)
    for (let i = 0; i < 3; i++) {
      if (i) await page.getByRole('checkbox', { name: /این پیشنهاد را برای همین نسخه/ }).check()
      await page.getByLabel('فروشنده', { exact: true }).fill(`فروشندهٔ مصنوعی ${i + 1}`)
      await page.getByLabel('لینک صفحهٔ پیشنهاد').fill(`https://merchant${i + 1}.example/synthetic-tv`)
      await page.getByLabel('قیمت مشاهده‌شده').fill(['۱۵۰۰۰۰۰۰۰', '۱۴۰۰۰۰۰۰', '۱۳۰۰۰۰۰۰'][i])
      await page.getByLabel('واحد مبلغ اصلی').selectOption(i ? 'TOMAN' : 'IRR')
      await page.getByLabel('موجودی مشاهده‌شده').selectOption(i === 2 ? 'OUT_OF_STOCK' : 'IN_STOCK')
      if (i === 1) {
        await page.getByLabel('هزینهٔ ارسال (تومان)').fill('۲۰۰۰۰')
        await page.getByLabel('هزینه‌های اجباری (تومان)').fill('٠')
      }
      await page.getByLabel('زمان مشاهدهٔ شما').fill(observed)
      const saved = page.waitForResponse(r => r.url().endsWith('/choices/manual-offers') && r.request().method() === 'POST')
      await page.getByRole('button', { name: 'ثبت پیشنهاد دستی' }).click()
      expect((await saved).status()).toBe(201)
      await expect(page.getByRole('region', { name: 'مقایسهٔ قیمت‌های ثبت‌شده' }).locator('.attached-offer')).toHaveCount(i + 1)
    }
    await page.getByText('ثبت پیشنهادی که خودم دیده‌ام', { exact: true }).click()
    const offers = page.getByRole('region', { name: 'مقایسهٔ قیمت‌های ثبت‌شده' })
    await expect(offers).toContainText('۱۴٬۰۲۰٬۰۰۰ تومان')
    await expect(offers).toContainText('۱۵۰٬۰۰۰٬۰۰۰ ریال')
    await expect(offers).toContainText('مبلغ نهایی: نامعلوم')
    await expect(offers).toContainText('ناموجود')
    await expect(offers).toContainText('زمان ثبت در برنامه')
    await expect(offers.getByText('واردشده توسط کاربر؛ مستقلاً تأیید نشده', { exact: true })).toHaveCount(3)
    await expect(offers.getByRole('link')).toHaveCount(3)
    for (const link of await offers.getByRole('link').all()) {
      expect(await link.getAttribute('href')).toMatch(/^https:\/\/merchant[123]\.example\/synthetic-tv$/)
      await expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    }
    await page.reload()
    await page.getByRole('button', { name: /ادامهٔ گفت‌وگو/ }).click()
    await expect(page.getByRole('heading', { name: 'همراه خرید', exact: true })).toBeVisible()
    if (width === 390) await page.getByRole('button', { name: 'میز انتخاب', exact: true }).click()
    await expect(offers.locator('.attached-offer')).toHaveCount(3)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    const axe = await new AxeBuilder({ page }).analyze()
    expect(axe.violations.filter(v => ['serious', 'critical'].includes(v.impact ?? ''))).toEqual([])
    await offers.scrollIntoViewIfNeeded()
    const dir = resolve('artifacts/screenshots')
    await mkdir(dir, { recursive: true })
    await page.screenshot({ path: resolve(dir, `market-manual-${width}.png`), fullPage: true })
  })
}
