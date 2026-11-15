import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

import { expect, test } from '../../frontend/tests/support/playwright-fixtures'

const screenshots = resolve(process.env.COPILOT_SCREENSHOT_DIR ?? '../artifacts/screenshots')
test.beforeAll(async () => { await mkdir(screenshots, { recursive: true }) })

async function prepareChoice(page: import('@playwright/test').Page, options: {
  category: 'electronics' | 'sports'; budget: string; criterion?: string; intended?: string; intent?: string
}) {
  await page.goto('/copilot')
  await expect(page.locator('.new-conversation')).toBeEnabled({ timeout: 20_000 })
  await page.locator('.new-conversation').click()
  await page.getByRole('button', { name: 'ویرایش brief' }).click()
  await page.getByRole('combobox', { name: 'مخاطب', exact: true }).selectOption('SELF')
  await page.getByLabel('دسته', { exact: true }).fill(options.category)
  await page.getByLabel('سقف بودجه (تومان)').fill(options.budget)
  if (options.intent) await page.getByRole('combobox', { name: 'هدف خرید', exact: true }).selectOption(options.intent)
  if (options.criterion) {
    await page.getByRole('combobox', { name: options.criterion, exact: true }).selectOption('HARD')
  }
  await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
  await page.getByRole('button', { name: 'تأیید brief برای پژوهش' }).click()
  await page.getByRole('combobox', { name: 'دستهٔ نمونهٔ آموزشی' }).selectOption(options.category)
  await page.getByRole('button', { name: 'بارگذاری دادهٔ مصنوعی' }).click()
  const intended = page.getByRole('combobox', { name: 'محصول موردنظر' })
  await expect(intended).toBeEnabled()
  if (options.intended) {
    await intended.selectOption({ label: options.intended })
    for (const checkbox of await page.getByRole('checkbox').all()) await checkbox.check()
  }
  await page.getByRole('button', { name: 'ساخت مقایسه' }).click()
  await expect(page.locator('.comparison-card')).toHaveCount(3)
}

async function ask(page: import('@playwright/test').Page, message: string) {
  await page.getByRole('textbox', { name: 'پیام شما' }).fill(message)
  await page.getByRole('button', { name: 'ارسال پیام' }).click()
  await expect(page.getByText(message, { exact: true })).toBeVisible()
  await expect(page.getByText('پاسخ کامل شد.', { exact: true })).toBeVisible({ timeout: 20_000 })
}

test('synthetic conversation 1: asks for a supported alternative', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await prepareChoice(page, { category: 'electronics', budget: '10000000' })
  await ask(page, 'چه جایگزینی در همین مقایسه داری؟')
  await expect(page.getByText(/رایانهٔ نمایشی پ.*جایگزین پشتیبانی‌شده/)).toBeVisible()
  await expect(page.locator('.message.assistant').last()).toContainText('۹٬۰۰۰٬۰۰۰ تومان')
  await page.screenshot({ path: resolve(screenshots, 'copilot-phase11-1-alternative.png'), fullPage: true })
  await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
  await page.getByRole('button', { name: 'بررسی صریح مدل‌های حساب' }).click()
  await expect(page.getByRole('alert')).toContainText('فهرست حساب در منطقهٔ فعلی قابل بازیابی نیست')
})

test('synthetic conversation 2: explains an evidenced mismatch', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await prepareChoice(page, {
    category: 'electronics', budget: '10000000', criterion: 'قابل‌حمل بودن',
    intended: 'رایانهٔ نمایشی ب', intent: 'ENJOYMENT',
  })
  await ask(page, 'چرا این گزینه با نیاز من هم‌خوان نیست؟')
  await expect(page.getByText(/رایانهٔ نمایشی ب.*قابل‌حمل بودن.*هم‌خوان نیست/)).toBeVisible()
  await page.screenshot({ path: resolve(screenshots, 'copilot-phase11-1-mismatch.png'), fullPage: true })
})

test('synthetic conversation 3: keeps unsupported product facts unknown', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await prepareChoice(page, {
    category: 'sports', budget: '2000000', criterion: 'ضدآب بودن', intended: 'کفش نمایشی پ',
  })
  await ask(page, 'برای تصمیم چه چیزی هنوز نامعلوم است؟')
  await expect(page.getByText(/کفش نمایشی پ.*ضدآب بودن هنوز نامعلوم است/)).toBeVisible()
  await expect(page.getByText(/ضدآب بودن را از منبع معتبر بررسی کنید/)).toBeVisible()
  await page.screenshot({ path: resolve(screenshots, 'copilot-phase11-1-unknown.png'), fullPage: true })
})
