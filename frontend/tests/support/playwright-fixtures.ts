import { expect, test as base } from '@playwright/test'

export { expect }

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /قبل از خرید/ })).toBeVisible()
    await use(page)
  },
})
