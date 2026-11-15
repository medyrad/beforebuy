import { expect, test as base } from '@playwright/test'

export { expect }

export const test = base.extend({
  page: async ({ page }, use) => {
    const ready = page.waitForResponse(response => response.url().endsWith('/api/v1/copilot/settings') && response.status() === 200, { timeout: 30000 })
    await page.goto('/')
    await ready
    await expect(page.getByRole('heading', { name: 'برای چه خریدی کمکت کنم؟' })).toBeVisible()
    await use(page)
  },
})
