import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const screenshotDirectory = resolve(process.env.COPILOT_SCREENSHOT_DIR ?? '../artifacts/screenshots')

test.beforeAll(async () => { await mkdir(screenshotDirectory, { recursive: true }) })

async function createConversation(page: import('@playwright/test').Page) {
  await page.goto('/copilot')
  await expect(page.getByRole('heading', { name: 'همراه خرید' })).toBeVisible()
  await expect(page.locator('.new-conversation')).toBeEnabled()
  await page.locator('.new-conversation').click()
  await expect(page.getByRole('textbox', { name: 'پیام شما' })).toBeEnabled()
}

test('real proxy fixture stream, brief edit, accessibility and desktop visual', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await createConversation(page)
  await page.getByRole('button', { name: 'ویرایش brief' }).click()
  await page.getByLabel('مخاطب').selectOption('SELF')
  await page.getByRole('textbox', { name: 'دسته', exact: true }).fill('لپ‌تاپ')
  await page.getByLabel('سقف بودجه (تومان)').fill('۷۰٬۰۰۰٬۰۰۰')
  await page.getByLabel('کاربردها، جدا با «،»').fill('برنامه‌نویسی، سفر')
  await page.getByRole('button', { name: 'ذخیره' }).click()
  await expect(page.getByText('۷۰٬۰۰۰٬۰۰۰ تومان')).toBeVisible()

  const message = 'نیاز من ثبت شود؛ نام مدل Example X <script>alert(1)</script> است.'
  await page.getByRole('textbox', { name: 'پیام شما' }).fill(message)
  await page.getByRole('button', { name: 'ارسال پیام' }).click()
  await expect(page.getByText(/fixture توسعه است/)).toBeVisible()
  await expect(page.getByText(message)).toBeVisible()
  await expect(page.getByText('بدون AI زنده')).toBeVisible()
  await page.getByText('پژوهش منابع و پیشنهادهای فروش', { exact: true }).click()
  await expect(page.getByRole('heading', { name: 'پیشنهادهای واقعی و منبع‌دار' })).toBeVisible()
  await expect(page.getByText(/پوشش همهٔ بازار/)).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  const axe = await new AxeBuilder({ page }).analyze()
  expect(axe.violations.filter((item) => ['critical', 'serious'].includes(item.impact ?? ''))).toEqual([])
  await page.screenshot({ path: resolve(screenshotDirectory, 'copilot-phase8-desktop-1440.png'), fullPage: true })
  await page.reload()
  await expect(page.getByRole('heading', { name: 'همراه خرید' })).toBeVisible()
})

test('mobile pane switching preserves state and keyboard controls remain reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await createConversation(page)
  await page.getByRole('textbox', { name: 'پیام شما' }).fill('پیش‌نویس حفظ‌شونده')
  await page.getByRole('button', { name: 'میز انتخاب' }).click()
  await expect(page.getByRole('main')).toHaveClass(/mobile-active/)
  await page.getByRole('button', { name: 'گفت‌وگو' }).click()
  await expect(page.getByRole('textbox', { name: 'پیام شما' })).toHaveValue('پیش‌نویس حفظ‌شونده')
  await page.keyboard.press('Tab')
  expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe('BODY')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  const axe = await new AxeBuilder({ page }).analyze()
  expect(axe.violations.filter((item) => ['critical', 'serious'].includes(item.impact ?? ''))).toEqual([])
  await page.getByRole('button', { name: 'میز انتخاب' }).click()
  await page.screenshot({ path: resolve(screenshotDirectory, 'copilot-phase8-mobile-390.png'), fullPage: true })
})

test('captured offer regression is explicitly labelled and responsive', async ({ page }) => {
  const offer = {
    id: 'offer-captured-1', variant_id: 'variant-captured-1', product_name: 'سرخ‌کن فیلیپس NA230', seller: 'فروشگاه نمونهٔ ثبت‌شده',
    source_name: 'captured.example', source_url: 'https://captured.example/product/na230', merchant_url: 'https://captured.example/product/na230',
    item_price: 239900000, source_currency: 'IRR', price_toman: 23990000, shipping_toman: null,
    mandatory_charges_toman: null, total_payable_toman: null, warranty: null, availability: 'IN_STOCK',
    observation_kind: 'MERCHANT_PAGE_VERIFIED', evidence_state: 'CAPTURED_FIXTURE',
    observed_at: '2026-11-15T08:00:00+03:30', fresh_until: '2026-11-15T14:00:00+03:30',
  }
  const job = { id: 'job-fixture', status: 'SUCCESS', stage: 'COMPLETED', completed: 1, total: 1, request_count: 0,
    coverage: { extracted: ['captured.example'], blocked: [], failed: [], mode: 'FIXTURE' }, offers: [offer] }
  await page.route('**/api/v1/conversations/*/research', async (route) => {
    await route.fulfill({ status: 202, contentType: 'application/json', body: JSON.stringify({
      job, operation: { id: 'fixture-operation', status: 'COMPLETED' }, events_url: '/events', idempotent_replay: false,
    }) })
  })
  await page.setViewportSize({ width: 390, height: 844 })
  await createConversation(page)
  await page.getByRole('button', { name: 'میز انتخاب' }).click()
  await page.getByText('پژوهش منابع و پیشنهادهای فروش', { exact: true }).click()
  await page.getByRole('textbox', { name: 'لینک‌های دقیق محصول' }).fill('https://captured.example/product/na230')
  await page.getByRole('button', { name: 'بررسی پیشنهادها' }).click()
  await expect(page.getByText('۲۳٬۹۹۰٬۰۰۰ تومان')).toBeVisible()
  await expect(page.getByText('ثبت واقعیِ تاریخی')).toBeVisible()
  await expect(page.getByText(/هزینهٔ ارسال و مبلغ نهایی نامعلوم/)).toBeVisible()
  await expect(page.getByText('کمترین قیمت بین منابع بررسی‌شده')).toBeVisible()
  await page.screenshot({ path: resolve(screenshotDirectory, 'copilot-phase9-2-captured-offer-mobile.png'), fullPage: true })
})

test('legacy default route remains available', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /قبل از خرید/ })).toBeVisible()
})
