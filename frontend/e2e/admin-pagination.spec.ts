import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { login } from './helpers'

async function setup(page: Page, count: number, fail = false) {
  let departments = Array.from({ length: count }, (_, index) => ({
    id: index + 1, code: `D${index + 1}`, name: `Department ${index + 1}`,
    description: null, is_active: true, created_at: '2026-09-01T00:00:00Z',
  }))
  const offsets: number[] = []
  const deletions: number[] = []
  await page.route('**/api/v1/**', async route => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/v1', '')
    if (path === '/auth/login') {
      await route.fulfill({ json: { access_token: 'admin-pagination-token', token_type: 'bearer' } })
    } else if (path === '/auth/me') {
      await route.fulfill({ json: { id: 1, first_name: 'Admin', last_name: 'Test', email: 'admin.e2e@example.com', role: 'admin', is_active: true } })
    } else if (path === '/departments' && request.method() === 'GET') {
      const skip = Number(url.searchParams.get('skip') || 0)
      offsets.push(skip)
      await route.fulfill({ json: departments.slice(skip, skip + 20) })
    } else if (path.startsWith('/departments/') && request.method() === 'DELETE') {
      const id = Number(path.split('/').pop())
      deletions.push(id)
      if (fail) await route.fulfill({ status: 409, json: { detail: 'Deactivation failed.' } })
      else {
        departments = departments.filter(department => department.id !== id)
        await route.fulfill({ status: 204 })
      }
    } else throw new Error(`Unexpected API request: ${request.method()} ${path}`)
  })
  await login(page, 'admin')
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Departments', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Deactivate #1', exact: true })).toBeVisible()
  return { offsets, deletions }
}

async function deactivate(page: Page, id: number) {
  await page.getByRole('button', { name: `Deactivate #${id}`, exact: true }).click()
  await page.getByRole('button', { name: 'Confirm deactivation', exact: true }).click()
}

const success = 'Record deactivated. The database record has been retained.'

// A short bounded observation also catches loaders that keep refetching after settling.
async function expectStableRequests(page: Page, offsets: number[], expected: number[]) {
  expect(offsets).toEqual(expected)
  await page.waitForTimeout(300)
  expect(offsets).toEqual(expected)
}

test('deactivating sole department on page 2 returns to page 1 with all 20 remaining records', async ({ page }) => {
  const { offsets, deletions } = await setup(page, 21)
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(page.getByText('Page 2', { exact: true })).toBeVisible()
  await deactivate(page, 21)
  await expect(page.getByText('Page 1', { exact: true })).toBeVisible()
  await expect(page.getByRole('row')).toHaveCount(21)
  for (let id = 1; id <= 20; id++) {
    await expect(page.getByRole('cell', { name: `Department ${id}`, exact: true })).toBeVisible()
  }
  await expect(page.getByRole('button', { name: 'Deactivate #21', exact: true })).toHaveCount(0)
  await expect(page.getByRole('status')).toHaveText(success)
  await expect(page.getByRole('button', { name: 'Previous', exact: true })).toBeDisabled()
  expect(deletions).toEqual([21])
  await expectStableRequests(page, offsets, [0, 20, 20, 0])
})

test('deactivating sole department on page 1 keeps a valid empty first page', async ({ page }) => {
  const { offsets } = await setup(page, 1)
  await deactivate(page, 1)
  await expect(page.getByText('No records on this page.', { exact: true })).toBeVisible()
  await expect(page.getByText('Page 1', { exact: true })).toBeVisible()
  await expect(page.getByRole('status')).toHaveText(success)
  await expect(page.getByRole('button', { name: 'Previous', exact: true })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled()
  await expectStableRequests(page, offsets, [0, 0])
})

test('failed deactivation keeps page 2 and its department without refetching', async ({ page }) => {
  const { offsets, deletions } = await setup(page, 21, true)
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(page.getByText('Page 2', { exact: true })).toBeVisible()
  await deactivate(page, 21)
  await expect(page.getByRole('alert')).toHaveText('Deactivation failed.')
  await expect(page.getByText('Page 2', { exact: true })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'Department 21', exact: true })).toBeVisible()
  await expect(page.getByText(success, { exact: true })).toHaveCount(0)
  expect(deletions).toEqual([21])
  await expectStableRequests(page, offsets, [0, 20])
})
