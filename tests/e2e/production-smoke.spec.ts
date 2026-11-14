import { completeAnalysis } from '../../frontend/tests/support/e2e-helpers'
import { expect, test } from '../../frontend/tests/support/playwright-fixtures'

test('production HTTPS same-origin journey and direct SPA route', async ({ page }) => {
  await expect(page).toHaveURL(/^https:/)
  await completeAnalysis(page, { product: 'مدل مصنوعی تمرین M4' })
  await expect(page.getByRole('status')).toContainText('نسخهٔ نمایشی')
  const reportUrl = page.url()

  await page.locator('.rating-row label').filter({ hasText: '۴' }).click()
  await expect(page.getByRole('radio', { name: '۴' })).toBeChecked()
  await page.getByRole('button', { name: 'اصلاح پاسخ‌ها' }).click()
  await page.getByRole('button', { name: 'ادامه' }).click()
  await page.getByRole('button', { name: 'ادامه' }).click()
  await page.getByRole('radio', { name: 'صفر تومان' }).check()
  await page.getByRole('button', { name: 'نمایش تحلیل' }).click()
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()

  await page.goto(reportUrl)
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'قیمت بالاتر از بودجه است' })).toBeVisible()
  await page.getByRole('button', { name: 'تاریخچه' }).click()
  await expect(page.locator('.history-item')).toHaveCount(1)
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /حذف تحلیل/ }).click()
  await expect(page.getByText('هنوز تحلیلی ندارید')).toBeVisible()
})
