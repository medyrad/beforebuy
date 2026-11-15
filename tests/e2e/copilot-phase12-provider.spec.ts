import { expect, test } from '../../frontend/tests/support/playwright-fixtures'

test('GapGPT settings are explicit while ordinary Persian chat stays mock and offline', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/copilot')
  await expect(page.locator('.new-conversation')).toBeEnabled({ timeout: 20_000 })

  await page.getByRole('button', { name: 'تنظیمات دستیار', exact: true }).click()
  await expect(page.getByRole('combobox', { name: 'ارائه‌دهنده' })).toHaveValue('gapgpt')
  await expect(page.getByLabel('مدل مستندشده')).toHaveValue('gapgpt-deepseek-v4.1-flash')
  await expect(page.getByText(/میزبانی‌شده در ایران/)).toBeVisible()
  await page.getByRole('button', { name: 'بررسی صریح مدل‌های حساب' }).click()
  await expect(page.getByRole('alert')).toContainText('ابتدا کلید GapGPT را ذخیره کنید')

  await page.getByRole('button', { name: 'میز خرید', exact: true }).click()
  await page.getByRole('button', { name: 'گفت‌وگوی تازه', exact: true }).last().click()
  const message = 'گوشی من خراب شده و برای هدیه دنبال انتخاب مطمئن‌تری هستم؛ از کجا شروع کنیم؟'
  await page.getByRole('textbox', { name: 'پیام شما' }).fill(message)
  await page.getByRole('button', { name: 'ارسال پیام' }).click()
  await expect(page.getByText(message, { exact: true })).toBeVisible()
  await expect(page.getByText('پاسخ کامل شد.', { exact: true })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText(/حالت توسعه|fixture/).first()).toBeVisible()
})
