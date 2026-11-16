import { test, expect } from '@playwright/test'
test.use({ trace: 'off', screenshot: 'off', video: 'off' })
for (const width of [390, 1440]) {
  test(`OpenRouter isolated encrypted storage and blocked pilot behind NGINX ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/copilot')
    await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
    const provider = page.getByRole('combobox', { name: 'ارائه‌دهنده', exact: true })
    await provider.selectOption('openrouter')
    await page.getByLabel('کلید OpenRouter', { exact: true }).fill('synthetic-openrouter-browser-only')
    await page.getByRole('button', { name: 'ذخیرهٔ کلید', exact: true }).click()
    await expect(page.getByText('ذخیره‌شده؛ اعتبارسنجی نشده', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'آزمایش رایگان', exact: true })).toBeDisabled()
    for (const other of ['openai', 'gapgpt']) {
      await provider.selectOption(other)
      await expect(page.getByText('کلیدی ذخیره نشده', { exact: true })).toBeVisible()
    }
    await provider.selectOption('openrouter')
    await expect(page.getByText('ذخیره‌شده؛ اعتبارسنجی نشده', { exact: true })).toBeVisible()
    await page.getByRole('checkbox').check()
    await page.getByRole('button', { name: 'آزمایش رایگان', exact: true }).click()
    await expect(page.getByRole('alert')).toContainText('صلاحیت خدمت و مسیر Baidu')
    await page.reload()
    await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
    await expect(provider).toHaveValue('openrouter')
    await page.getByRole('button', { name: 'حذف کلید', exact: true }).click()
    await expect(page.getByText('کلیدی ذخیره نشده', { exact: true })).toBeVisible()
  })
}
