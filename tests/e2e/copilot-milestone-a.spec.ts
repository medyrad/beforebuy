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
  await page.getByLabel('دسته').fill('لپ‌تاپ')
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
  await expect(page.getByRole('heading', { name: 'هنوز گزینه‌ای برای مقایسه نداریم.' })).toBeVisible()
  await expect(page.getByText(/قیمت بازار/)).toHaveCount(1) // only the honest not-implemented disclosure
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

test('legacy default route remains available', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /قبل از خرید/ })).toBeVisible()
})
