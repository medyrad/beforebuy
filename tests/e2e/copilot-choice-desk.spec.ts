import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const screenshots = resolve(process.env.COPILOT_SCREENSHOT_DIR ?? '../artifacts/screenshots')
test.beforeAll(async () => { await mkdir(screenshots, { recursive: true }) })

for (const width of [1440, 390]) {
  test(`labelled real database comparison through NGINX at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/copilot')
    await expect(page.locator('.new-conversation')).toBeEnabled({ timeout: 20000 })
    await page.locator('.new-conversation').click()
    await expect(page.getByRole('textbox', { name: 'پیام شما' })).toBeEnabled()
    await page.getByRole('textbox', { name: 'پیام شما' }).fill('پیش‌نویس آزمایشی بدون دادهٔ شخصی')
    if (width === 390) await page.getByRole('button', { name: 'میز انتخاب', exact: true }).click()
    await page.getByRole('button', { name: 'ویرایش brief' }).click()
    await page.getByRole('combobox', { name: 'مخاطب', exact: true }).selectOption('SELF')
    await page.getByLabel('دسته', { exact: true }).fill('electronics')
    await page.getByLabel('سقف بودجه (تومان)').fill('10000000')
    await page.getByRole('combobox', { name: 'هدف خرید', exact: true }).selectOption('ENJOYMENT')
    await page.getByRole('combobox', { name: 'قابل‌حمل بودن', exact: true }).selectOption('HARD')
    await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
    await page.getByRole('button', { name: 'تأیید brief برای پژوهش' }).click()
    await expect(page.getByRole('button', { name: 'بارگذاری دادهٔ مصنوعی' })).toBeEnabled()
    await page.getByRole('button', { name: 'بارگذاری دادهٔ مصنوعی' }).click()
    await expect(page.getByRole('button', { name: 'ساخت مقایسه' })).toBeEnabled()
    await page.getByRole('button', { name: 'ساخت مقایسه' }).click()
    await expect(page.getByRole('heading', { name: 'شواهد، برندهٔ یکتا نشان نمی‌دهند' })).toBeVisible()
    await expect(page.locator('.comparison-card')).toHaveCount(3)
    if (width === 1440) {
      const rail = await page.locator('.conversation-pane').boundingBox()
      const desk = await page.locator('.choice-desk').boundingBox()
      expect(rail!.x).toBeGreaterThan(desk!.x)
    }
    await expect(page.getByText(/لذت‌بردن از خرید هدف معتبری است/)).toBeVisible()
    const source = page.getByRole('button', { name: /شواهد و منابع/ }).first()
    await source.focus(); await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('dialog')).toContainText('دادهٔ مصنوعی آموزشی')
    await expect(page.getByRole('button', { name: 'بستن منابع' })).toBeFocused()
    await page.keyboard.press('Tab')
    expect(await page.evaluate(() => !!document.activeElement?.closest('dialog'))).toBe(true)
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).not.toBeVisible()
    await expect(source).toBeFocused()
    await page.locator('.comparison-card').first().getByText('نامعلوم‌ها و آنچه می‌تواند نتیجه را تغییر دهد', { exact: true }).click()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    const axe = await new AxeBuilder({ page }).analyze()
    expect(axe.violations.filter((v) => ['critical', 'serious'].includes(v.impact ?? ''))).toEqual([])
    await page.screenshot({ path: resolve(screenshots, `copilot-phase10-${width}.png`), fullPage: true })

    await page.getByRole('button', { name: 'ویرایش brief' }).click()
    await page.getByLabel('سقف بودجه (تومان)').fill('8000000')
    await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
    await expect(page.getByText(/مقایسهٔ قبلی معتبر نیست/)).toBeVisible()
    await expect(page.locator('.comparison-card')).toHaveCount(0)
    await page.getByRole('button', { name: 'تأیید brief برای پژوهش' }).click()
    await page.getByRole('button', { name: 'ساخت مقایسه' }).click()
    await expect(page.getByRole('heading', { name: 'یک انتخاب با پشتوانهٔ نیازهای معلوم' })).toBeVisible()
    await page.evaluate(() => { document.documentElement.style.zoom = '2' })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    const zoomAxe = await new AxeBuilder({ page }).analyze()
    expect(zoomAxe.violations.filter((v) => ['critical', 'serious'].includes(v.impact ?? ''))).toEqual([])
    await page.evaluate(() => { document.documentElement.style.zoom = '' })
    if (width === 390) await page.getByRole('button', { name: 'گفت‌وگو', exact: true }).click()
    await expect(page.getByRole('textbox', { name: 'پیام شما' })).toHaveValue('پیش‌نویس آزمایشی بدون دادهٔ شخصی')
    const cancelled = page.waitForResponse((response) => response.url().endsWith('/cancel') && response.request().method() === 'POST')
    // The fixture is intentionally short. Click the real stop control in the browser's
    // first DOM update, without a container/driver round trip that can outlast the stream.
    // No request, SSE event, or cancel response is mocked.
    await page.evaluate(() => new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => { observer.disconnect(); reject(new Error('Stop control did not appear during the real fixture stream')) }, 10000)
      const observer = new MutationObserver(() => {
        const stop = document.querySelector<HTMLButtonElement>('[aria-label="توقف تولید"]')
        if (stop) { observer.disconnect(); window.clearTimeout(timeout); stop.click(); resolve() }
      })
      observer.observe(document.body, { childList: true, subtree: true, attributes: true })
      document.querySelector<HTMLButtonElement>('[aria-label="ارسال پیام"]')!.click()
    }))
    expect((await (await cancelled).json()).status).toBe('CANCELLED')
    await expect(page.getByText('این اجرا کامل نشد.')).toBeVisible()
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /قبل از خرید/ })).toBeVisible()
  })
}
