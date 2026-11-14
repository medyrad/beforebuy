import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

import { completeAnalysis, seriousAccessibilityViolations } from '../../frontend/tests/support/e2e-helpers'
import { expect, test } from '../../frontend/tests/support/playwright-fixtures'

const screenshotDirectory = resolve(process.cwd(), '../artifacts/screenshots')

test.beforeAll(async () => { await mkdir(screenshotDirectory, { recursive: true }) })

test('Persian digits, follow-up cap, mock disclosure and mobile layout', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const longModel = 'Samsung Galaxy Example Ultra 5G 256GB — مدل آزمایشی با نام بسیار طولانی'
  await completeAnalysis(page, { product: longModel, price: '۱۲٬۵۰۰٬۰۰۰', state: 'serious', followUps: true })

  await expect(page.getByRole('status')).toContainText('نسخهٔ نمایشی')
  await expect(page.getByText(/هوش مصنوعی زنده نیست/)).toBeVisible()
  await expect(page.getByText(/مشخصات فنی این مدل تأیید نشده/)).toBeVisible()
  await expect(page.getByRole('heading', { name: 'جمع‌بندی برای تصمیم شما' })).toBeVisible()
  await expect(page.locator('.dimension-grid .dimension-card')).toHaveCount(4)
  await expect(page.getByRole('radio', { name: '۱، اصلاً کمک نکرد' })).toBeVisible()
  await expect(page.getByRole('radio', { name: '۵، خیلی کمک کرد' })).toBeVisible()
  await expect(page.getByText('TARGET_FIT_UNVERIFIED')).toHaveCount(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  expect(await seriousAccessibilityViolations(page)).toEqual([])
  await page.locator('#main').focus()
  await page.screenshot({ path: resolve(screenshotDirectory, 'phase-5.1-mobile-390-report.png'), fullPage: true })
})

test('zero budget and unknown budget remain distinct', async ({ page }) => {
  await completeAnalysis(page, { budget: 'zero' })
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()
  await expect(page.getByText('۰ تومان', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'صفحهٔ آغاز قبل از خرید' }).click()
  await completeAnalysis(page, { product: 'مدل با بودجه نامعلوم', budget: 'unknown' })
  await expect(page.getByRole('heading', { name: 'تعویض قابل توجیه است؛ بودجه نامعلوم است' })).toBeVisible()
  await expect(page.getByText('بودجه نامعلوم', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'تاریخچه' }).click()
  await expect(page.locator('.history-item')).toHaveCount(2)
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'پاک‌کردن همهٔ تاریخچه' }).click()
  await expect(page.getByText('هنوز تحلیلی ندارید')).toBeVisible()
})

test('feedback is invalidated by edit, retry is safe, and history survives refresh', async ({ page }) => {
  await completeAnalysis(page)
  await page.locator('.rating-row label').filter({ hasText: '۴' }).click()
  await expect(page.getByRole('radio', { name: '۴' })).toBeChecked()

  await page.getByRole('button', { name: 'اصلاح پاسخ‌ها' }).click()
  await page.getByRole('button', { name: 'ادامه' }).click()
  await page.getByRole('button', { name: 'ادامه' }).click()
  await page.getByRole('radio', { name: 'صفر تومان' }).check()
  await page.getByRole('button', { name: 'نمایش تحلیل' }).click()
  await expect(page.getByRole('radio', { name: '۴' })).not.toBeChecked()
  await page.getByRole('button', { name: 'تحلیل دوباره' }).click()
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()

  await page.reload()
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()
  await page.getByRole('button', { name: 'تاریخچه' }).click()
  await expect(page.locator('.history-item')).toHaveCount(1)
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /حذف تحلیل/ }).click()
  await expect(page.getByText('هنوز تحلیلی ندارید')).toBeVisible()
})

test('isolated browser contexts cannot read each other analyses', async ({ page, browser }) => {
  await completeAnalysis(page, { product: 'تحلیل خصوصی context A' })
  const privateUrl = page.url()

  const strangerContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5173', locale: 'fa-IR' })
  const strangerPage = await strangerContext.newPage()
  await strangerPage.goto(privateUrl)
  await expect(strangerPage.getByText(/در دسترس نیست/)).toBeVisible()
  await expect(strangerPage.getByRole('heading', { name: /قبل از خرید، نیاز و بودجه/ })).toBeVisible()
  await strangerContext.close()

  await page.getByRole('button', { name: 'تاریخچه' }).click()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /حذف تحلیل/ }).click()
})

test('test-only injected failure shows limited mode and desktop keyboard layout', async ({ browser }) => {
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    locale: 'fa-IR',
    viewport: { width: 1440, height: 960 },
    extraHTTPHeaders: { 'X-BeforeBuy-E2E-Explanation': 'limited' },
  })
  const page = await context.newPage()
  await page.goto('/')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'رفتن به محتوای اصلی' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'رفتن به محتوای اصلی' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main')).toBeFocused()

  await completeAnalysis(page, { product: 'Desktop Limited Mode Test Model 512GB' })
  await expect(page.getByRole('status')).toContainText('گزارش محدود')
  await expect(page.getByText(/جمع‌بندی اصلی همچنان معتبر است/)).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  expect(await seriousAccessibilityViolations(page)).toEqual([])
  await page.locator('#main').focus()
  await page.screenshot({ path: resolve(screenshotDirectory, 'phase-5.1-desktop-1440-limited.png'), fullPage: true })
  await context.close()
})
