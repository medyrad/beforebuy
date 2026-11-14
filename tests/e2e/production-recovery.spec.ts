import { writeFile } from 'node:fs/promises'

import { completeAnalysis } from '../../frontend/tests/support/e2e-helpers'
import { expect, test } from '../../frontend/tests/support/playwright-fixtures'

const recoveryState = process.env.BEFOREBUY_RECOVERY_STATE
const recoveryIdFile = process.env.BEFOREBUY_RECOVERY_ID_FILE

test('seed synthetic recovery evidence', async ({ page, context }) => {
  test.skip(!recoveryState || !recoveryIdFile, 'recovery artifact paths are required')
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /قبل از خرید/ })).toBeVisible()
  await completeAnalysis(page, { product: 'دادهٔ مصنوعی بازیابی M4' })
  await page.locator('.rating-row label').filter({ hasText: '۵' }).click()
  await expect(page.getByRole('radio', { name: '۵' })).toBeChecked()
  const id = new URL(page.url()).searchParams.get('analysis')
  expect(id).toBeTruthy()
  await context.storageState({ path: recoveryState! })
  await writeFile(recoveryIdFile!, `${id}\n`, { mode: 0o600 })
})

test('restored owner session can read synthetic analysis and feedback', async ({ browser }) => {
  test.skip(!recoveryState || !recoveryIdFile, 'recovery artifact paths are required')
  const id = (await import('node:fs/promises')).readFile(recoveryIdFile!, 'utf8').then((value) => value.trim())
  const context = await browser.newContext({
    baseURL: process.env.PLAYWRIGHT_BASE_URL,
    storageState: recoveryState,
    ignoreHTTPSErrors: true,
    locale: 'fa-IR',
  })
  const page = await context.newPage()
  await page.goto(`/?analysis=${await id}`)
  await expect(page.getByText('دادهٔ مصنوعی بازیابی M4')).toBeVisible()
  await expect(page.getByRole('radio', { name: '۵' })).toBeChecked()
  await context.close()
})

test('delete synthetic recovery analysis from source after backup', async ({ browser }) => {
  test.skip(!recoveryState || !recoveryIdFile, 'recovery artifact paths are required')
  const context = await browser.newContext({
    baseURL: process.env.PLAYWRIGHT_BASE_URL,
    storageState: recoveryState,
    ignoreHTTPSErrors: true,
    locale: 'fa-IR',
  })
  const page = await context.newPage()
  await page.goto('/?view=history')
  await expect(page.getByText('دادهٔ مصنوعی بازیابی M4')).toBeVisible()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /حذف تحلیل/ }).click()
  await expect(page.getByText('هنوز تحلیلی ندارید')).toBeVisible()
  await context.close()
})
