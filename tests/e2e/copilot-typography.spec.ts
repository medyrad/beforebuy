import { test, expect, type Locator } from '@playwright/test'
import { resolve } from 'node:path'

// Isolated browser owner, synthetic text, no keys and no external inference.
test.use({ trace: 'off', screenshot: 'off', video: 'off', hasTouch: true })
const stage = process.env.TYPOGRAPHY_CAPTURE === 'before' ? 'before' : 'after'
async function typography(control: Locator, direction = 'rtl') {
  const style = await control.evaluate(el => {
    const s = getComputedStyle(el)
    return { family: s.fontFamily, size: s.fontSize, weight: s.fontWeight, line: s.lineHeight, direction: s.direction,
      nativeSelect: el.tagName === 'SELECT', height: el.getBoundingClientRect().height }
  })
  console.log(await control.getAttribute('aria-label') ?? await control.evaluate(el => el.tagName), style)
  expect.soft(style.family).toContain('Vazirmatn')
  expect.soft(style.size).toBe('16px')
  expect.soft(style.weight).toBe('400')
  // Chromium reports normal for native single-line select even with an explicit
  // line-height. Keep its platform picker; verify the actual usable control height.
  if (style.nativeSelect) {
    expect.soft(['normal', '28px']).toContain(style.line)
    expect.soft(style.height).toBeGreaterThanOrEqual(44)
  } else expect.soft(style.line).toBe('28px')
  expect.soft(style.direction).toBe(direction)
}
for (const width of [390, 1440]) {
  test(`native controls typography, keyboard and touch at ${width}`, async ({ page }) => {
    test.setTimeout(120000)
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/copilot')
    await expect(page.getByRole('textbox', { name: 'پیام شما' })).toBeEnabled({ timeout: 30000 })
    await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).tap()
    const provider = page.getByRole('combobox', { name: 'ارائه‌دهنده', exact: true })
    const model = page.getByRole('combobox', { name: 'مدل مستندشده', exact: true })
    await expect(provider).toBeEnabled()
    await expect(page.getByLabel('کلید GapGPT', { exact: true })).toBeVisible()
    await page.evaluate(() => document.fonts.ready)
    expect(await page.evaluate(() => document.fonts.check('16px Vazirmatn'))).toBe(true)
    await page.screenshot({ path: resolve(`artifacts/screenshots/typography-${stage}-settings-${width}.png`), fullPage: true })
    await typography(provider)
    await typography(model)
    await typography(page.getByLabel('کلید GapGPT', { exact: true }), 'ltr')
    await typography(page.getByRole('button', { name: 'ذخیرهٔ کلید', exact: true }))
    await model.scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(`artifacts/screenshots/typography-${stage}-model-${width}.png`) })
    await provider.focus()
    await page.keyboard.press('Escape')
    await expect(provider).toBeFocused()
    await expect(provider).toHaveCSS('outline-style', 'solid')
    await provider.tap()
    await page.keyboard.press('Escape')
    await expect(provider).toBeFocused()
    // Native type-ahead avoids assuming an OS-specific popup key sequence.
    await provider.press('o')
    await expect(provider).toHaveValue('openai')
    await expect(page.getByLabel('کلید OpenAI', { exact: true })).toBeVisible()
    await expect(model).toBeEnabled()
    await expect(model).toHaveValue('gpt-6-luna')
    await model.selectOption('gpt-6-luna')
    await expect(model).toBeEnabled()
    await provider.selectOption('gapgpt')
    await expect(page.getByLabel('کلید GapGPT', { exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    const box = await model.boundingBox()
    expect(box!.x).toBeGreaterThanOrEqual(0)
    expect(box!.x + box!.width).toBeLessThanOrEqual(width)
    await page.getByRole('button', { name: 'میز خرید', exact: true }).click()
    await page.getByRole('textbox', { name: 'پیام شما' }).fill('بودجه‌ام ۱۵ میلیون تومان است')
    await page.getByRole('button', { name: 'ارسال پیام' }).click()
    await expect(page.locator('.message.assistant:not(.provisional)')).toHaveCount(1, { timeout: 30000 })
    if (width === 390) await page.getByRole('button', { name: 'میز انتخاب', exact: true }).click()
    await page.getByRole('button', { name: 'اصلاح نیاز خرید' }).click()
    await page.getByRole('combobox', { name: 'مخاطب', exact: true }).selectOption('SELF')
    await page.getByLabel('دسته', { exact: true }).fill('home')
    await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
    await page.getByRole('button', { name: 'تأیید نیاز خرید', exact: true }).click()
    await page.getByText('آشنایی با مقایسه از طریق نمونهٔ آموزشی', { exact: true }).click()
    const category = page.getByRole('combobox', { name: 'دستهٔ نمونهٔ آموزشی', exact: true })
    await category.selectOption('home')
    await expect(category).toHaveValue('home')
    await category.scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(`artifacts/screenshots/typography-${stage}-category-${width}.png`) })
    await typography(category)
    await category.tap()
    await page.keyboard.press('Escape')
    await expect(category).toBeFocused()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  })
}
