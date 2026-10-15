import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { login } from './helpers'

// Catalog edge cases use API fixtures within the shared E2E runner.
// The academic-flow spec continues to exercise enrollment against the real API.

const offering = (id: number, is_open = true) => ({
  id, course_id: id, term_id: 1, professor_id: 1, professor_name: 'Professor Test',
  section: 'A', capacity: 25, is_open,
})
const record = (id: number, status = 'enrolled') => ({
  id, student_id: 1, course_offering_id: id, status, enrolled_at: '2026-09-01T00:00:00Z',
})

async function setup(page: Page, options: {
  missing?: boolean; failure?: boolean; delayed?: boolean; many?: boolean
} = {}) {
  const requests: { method: string; path: string; search: string }[] = []
  const records = [record(1), record(4, 'dropped'), record(5, 'completed')]
  let fail = options.failure
  let release = () => {}
  const gate = new Promise<void>(resolve => { release = resolve })
  await page.route('**/api/v1/**', async route => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/v1', '')
    requests.push({ method: request.method(), path, search: url.search })
    let body: unknown
    let status = 200
    if (path === '/auth/login') body = { access_token: 'catalog-test-token', token_type: 'bearer' }
    else if (path === '/auth/me') body = { id: 1, first_name: 'Student', last_name: 'Test', email: 'student.e2e@example.com', role: 'student', is_active: true }
    else if (path === '/students/me') {
      status = options.missing ? 404 : 200
      body = options.missing ? { detail: 'Student profile not found' } : { id: 1, user_id: 1 }
    } else if (path === '/enrollments/me') {
      if (options.delayed) await gate
      status = fail ? 503 : 200
      body = fail ? {} : records
    } else if (path === '/enrollments' && request.method() === 'POST') {
      body = record(request.postDataJSON().course_offering_id)
      records.push(body as ReturnType<typeof record>)
      status = 201
    } else if (path === '/course-offerings') {
      const skip = Number(url.searchParams.get('skip') || 0)
      body = options.many
        ? Array.from({ length: skip === 0 ? 20 : 1 }, (_, i) => offering(skip + i + 1))
        : [offering(1), offering(2), offering(4), offering(5),
          ...(url.searchParams.has('is_open') ? [] : [offering(3, false)])]
    } else if (path.startsWith('/courses/')) {
      const id = Number(path.split('/').pop())
      body = { id, code: `C${id}`, title: `Course ${id}`, credits: 3 }
    } else if (path === '/terms/1') body = { id: 1, name: 'Fall', academic_year: '2026-2027' }
    else throw new Error(`Unexpected API request: ${request.method()} ${path}`)
    await route.fulfill({ status, json: body })
  })
  await login(page, 'student')
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Courses', exact: true }).click()
  return { requests, release, recover: () => { fail = false } }
}
const card = (page: Page, id: number) => page.getByRole('article').filter({ has: page.getByRole('heading', { name: `C${id} · Course ${id}`, exact: true }) })
const posts = (requests: { method: string; path: string }[]) => requests.filter(r => r.method === 'POST' && r.path === '/enrollments')

test('persisted enrollment is disabled on initial load and reload; new enrollment updates immediately', async ({ page }) => {
  const { requests } = await setup(page)
  const enrolled = card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })
  await expect(enrolled).toBeDisabled()
  await enrolled.evaluate(button => (button as HTMLButtonElement).click())
  await page.getByRole('heading', { name: 'Course offerings', exact: true }).click()
  expect(posts(requests)).toHaveLength(0)
  const available = card(page, 2).getByRole('button', { name: 'Enroll', exact: true })
  await expect(available).toBeEnabled()
  await available.click()
  await expect(card(page, 2).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  await expect(page.getByRole('status')).toContainText('Enrollment successful.')
  expect(posts(requests)).toHaveLength(1)
  await page.reload()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  await expect(card(page, 2).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  expect(posts(requests)).toHaveLength(1)
})

test('open filter and closed offerings retain behavior without refetching enrollments', async ({ page }) => {
  const { requests } = await setup(page)
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  await expect(card(page, 3)).toHaveCount(0)
  for (const id of [4, 5]) await expect(card(page, id).getByRole('button', { name: 'Previously enrolled', exact: true })).toBeDisabled()
  await page.getByLabel('Show open offerings only').uncheck()
  await expect(card(page, 3).getByRole('button', { name: 'Closed', exact: true })).toBeDisabled()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  expect(requests.filter(r => r.path === '/enrollments/me')).toHaveLength(1)
  expect(posts(requests)).toHaveLength(0)
})

test('pagination reuses student enrollments and filtering resets the page', async ({ page }) => {
  const { requests } = await setup(page, { many: true })
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(card(page, 21)).toBeVisible()
  await expect(page.getByText('Page 2', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Previous', exact: true }).click()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(card(page, 21)).toBeVisible()
  await page.getByLabel('Show open offerings only').uncheck()
  await expect(page.getByText('Page 1', { exact: true })).toBeVisible()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  expect(requests.filter(r => r.path === '/enrollments/me')).toHaveLength(1)
  expect(requests.filter(r => r.path === '/students/me')).toHaveLength(1)
  expect(requests.some(r => r.path === '/course-offerings' && r.search.includes('skip=20'))).toBe(true)
})

test('missing profile disables enrollment without calling the enrollments API', async ({ page }) => {
  const { requests } = await setup(page, { missing: true })
  await expect(page.getByText('Create your student profile before enrolling.', { exact: false })).toBeVisible()
  await expect(card(page, 2).getByRole('button', { name: 'Enroll', exact: true })).toBeDisabled()
  expect(requests.filter(r => r.path === '/enrollments/me')).toHaveLength(0)
  expect(posts(requests)).toHaveLength(0)
})

test('waits for enrollment state before exposing enrollment controls', async ({ page }) => {
  const { requests, release } = await setup(page, { delayed: true })
  await expect(page.getByRole('status')).toHaveText('Loading course offerings…')
  await expect(page.getByRole('button', { name: 'Enroll', exact: true })).toHaveCount(0)
  expect(posts(requests)).toHaveLength(0)
  release()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
})

test('enrollment lookup failure blocks actions safely and supports retry', async ({ page }) => {
  const { requests, recover } = await setup(page, { failure: true })
  await expect(page.getByRole('alert')).toContainText('The request could not be completed. Please try again.')
  await expect(page.getByRole('button', { name: 'Enroll', exact: true })).toHaveCount(0)
  expect(posts(requests)).toHaveLength(0)
  recover()
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(card(page, 1).getByRole('button', { name: 'Enrolled', exact: true })).toBeDisabled()
  expect(requests.filter(r => r.path === '/enrollments/me')).toHaveLength(2)
  expect(requests.filter(r => r.path === '/course-offerings')).toHaveLength(1)
})

for (const [id, status] of [[1, 'enrolled'], [4, 'dropped'], [5, 'completed']] as const) {
  test(`${status} record blocks enrollment without a duplicate POST, including after reload`, async ({ page }) => {
    const { requests } = await setup(page)
    const button = card(page, id).getByRole('button', {
      name: status === 'enrolled' ? 'Enrolled' : 'Previously enrolled', exact: true,
    })
    await expect(button).toBeDisabled()
    await button.evaluate(element => (element as HTMLButtonElement).click())
    await page.getByRole('heading', { name: 'Course offerings', exact: true }).click()
    expect(posts(requests)).toHaveLength(0)
    await page.reload()
    await expect(button).toBeDisabled()
    expect(posts(requests)).toHaveLength(0)
  })
}
