import { test, expect } from '@playwright/test'

// Synthetic key only; never capture credential input in artifacts.
test.use({ trace: 'off', screenshot: 'off', video: 'off' })
for (const width of [390, 1440]) {
  test(`provider switching and encrypted OpenAI storage at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/copilot')
    await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
    const provider = page.getByRole('combobox', { name: 'ارائه‌دهنده', exact: true })
    await expect(provider).toBeEnabled()
    await provider.selectOption('openai')
    const key = page.getByLabel('کلید OpenAI', { exact: true })
    await expect(key).toBeVisible()
    await key.fill('synthetic-local-switch-test-only')
    await page.getByRole('button', { name: 'ذخیرهٔ کلید', exact: true }).click()
    await expect(page.getByText('ذخیره‌شده؛ اعتبارسنجی نشده', { exact: true })).toBeVisible()
    await expect(key).toHaveValue('')
    await provider.selectOption('gapgpt')
    await expect(page.getByText('کلیدی ذخیره نشده', { exact: true })).toBeVisible()
    await expect(page.getByLabel('مدل مستندشده')).toHaveValue('gapgpt-deepseek-v4.1-flash')
    await provider.selectOption('openai')
    await expect(page.getByText('ذخیره‌شده؛ اعتبارسنجی نشده', { exact: true })).toBeVisible()
    await page.reload()
    await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
    await expect(provider).toHaveValue('openai')
    await expect(page.getByText('ذخیره‌شده؛ اعتبارسنجی نشده', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'حذف کلید', exact: true }).click()
    await expect(page.getByText('کلیدی ذخیره نشده', { exact: true })).toBeVisible()
  })
}
