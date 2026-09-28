import { expect, test } from '@playwright/test'
import { login } from './helpers'

// One stateful scenario: retrying against partially created records is unsafe.
// Other specs retain the shared configuration's parallelism and CI retries.
test.describe.configure({ retries: 0 })

test('admin setup → student enrollment → professor grading → student results', async ({ page }) => {
  test.setTimeout(90_000)
  const course = 'E2E101 · End-to-End Software Engineering'
  const professor = 'E2E-PROF-001 · Professor · E2E Computer Science'
  const feedback = 'E2E grading workflow verified.'
  const navigation = page.getByRole('navigation', { name: 'Main navigation' })
  const navigate = async (name: string) => {
    await navigation.getByRole('link', { name, exact: true }).click()
  }
  const logout = async () => {
    await page.getByRole('button', { name: 'Log out' }).click()
    await expect(page).toHaveURL('/login')
  }
  const create = async () => {
    await page.getByRole('button', { name: 'Create', exact: true }).click()
    await expect(page.getByRole('status').filter({ hasText: /^Changes saved\.$/ })).toBeVisible()
  }

  await test.step('Admin creates department, assigned course, term and open offering', async () => {
    await login(page, 'admin')
    await navigate('Departments')
    await page.getByRole('button', { name: 'Create departments', exact: true }).click()
    await page.getByLabel('Code', { exact: true }).fill('E2ECS')
    await page.getByLabel('Name', { exact: true }).fill('E2E Computer Science')
    await create()
    await expect(page.getByRole('row').filter({ hasText: 'E2ECS' })).toContainText('E2E Computer Science')

    await navigate('Courses')
    await page.getByRole('button', { name: 'Create courses', exact: true }).click()
    await page.getByLabel('Code', { exact: true }).fill('E2E101')
    await page.getByLabel('Title', { exact: true }).fill('End-to-End Software Engineering')
    await page.getByLabel('Credits', { exact: true }).fill('3')
    await page.getByLabel('Department', { exact: true }).selectOption({ label: 'E2ECS · E2E Computer Science' })
    await page.getByLabel('Professor (optional)', { exact: true }).selectOption({ label: professor })
    await create()
    const courseRow = page.getByRole('row').filter({ hasText: 'E2E101' })
    await expect(courseRow).toContainText('End-to-End Software Engineering')
    await expect(courseRow).toContainText(professor)

    await navigate('Academic Terms')
    await page.getByRole('button', { name: 'Create academic terms', exact: true }).click()
    await page.getByLabel('Name', { exact: true }).fill('E2E Fall')
    await page.getByLabel('Academic year', { exact: true }).fill('2026-2027')
    await page.getByLabel('Start date', { exact: true }).fill('2026-09-01')
    await page.getByLabel('End date', { exact: true }).fill('2026-12-31')
    await create()
    await expect(page.getByRole('row').filter({ hasText: 'E2E Fall' })).toContainText('2026-2027')

    await navigate('Course Offerings')
    await page.getByRole('button', { name: 'Create course offerings', exact: true }).click()
    await page.getByLabel('Course', { exact: true }).selectOption({ label: course })
    await page.getByLabel('Professor', { exact: true }).selectOption({ label: professor })
    await page.getByLabel('Academic term', { exact: true }).selectOption({ label: 'E2E Fall · 2026-2027' })
    await page.getByLabel('Section', { exact: true }).fill('A')
    await page.getByLabel('Capacity', { exact: true }).fill('25')
    await page.getByLabel('Open for enrollment', { exact: true }).check()
    await create()
    const offeringRow = page.getByRole('row').filter({ hasText: course })
    for (const value of [professor, 'E2E Fall · 2026-2027', 'A', '25', 'Yes']) {
      await expect(offeringRow.getByRole('cell', { name: value, exact: true })).toBeVisible()
    }
    await logout()
  })

  await test.step('Student creates a profile and enrolls in the offering', async () => {
    await login(page, 'student')
    await navigate('Profile')
    for (const [label, value] of [
      ['Student number', 'E2E-STUDENT-001'], ['Department', 'E2E Computer Science'],
      ['Program', 'Software Engineering'], ['Year level', '1'],
      ['Enrollment year', '2026'], ['Expected graduation year', '2030'],
    ]) await page.getByLabel(label, { exact: true }).fill(value)
    await page.getByRole('button', { name: 'Create profile', exact: true }).click()
    await expect(page.getByRole('status')).toContainText('Your profile is ready.')
    await navigate('Courses')
    const offering = page.getByRole('article').filter({ has: page.getByRole('heading', { name: course, exact: true }) })
    await expect(offering.getByText('Open', { exact: true })).toBeVisible()
    await offering.getByRole('button', { name: 'Enroll', exact: true }).click()
    await expect(page.getByRole('status')).toContainText('Enrollment successful.')
    await navigate('Enrollments')
    await expect(page.getByRole('heading', { name: 'My enrollments', exact: true })).toBeVisible()
    const enrollment = page.getByRole('article').filter({ hasText: course })
    await expect(enrollment.getByText('enrolled', { exact: true })).toBeVisible()
    await logout()
  })

  await test.step('Professor verifies the roster and records a grade', async () => {
    await login(page, 'professor')
    await navigate('My Courses')
    await expect(page.getByRole('heading', { name: course, exact: true })).toBeVisible()
    // The scenario creates exactly one offering; no numeric ID is assumed.
    await page.getByRole('link', { name: 'View students →', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Student E2E', exact: true })).toBeVisible()
    await expect(page.getByText(/Student E2E-STUDENT-001 · Enrollment #\d+ · enrolled/)).toBeVisible()
    await page.getByRole('button', { name: 'Add grade', exact: true }).click()
    await page.getByLabel('Grade (0–100)', { exact: true }).fill('93.5')
    await page.getByLabel('Feedback (optional)', { exact: true }).fill(feedback)
    await page.getByRole('button', { name: 'Record grade', exact: true }).click()
    await expect(page.getByRole('status')).toHaveText('Grade recorded.')
    await expect(page.getByText('Grade: 93.5 / 100', { exact: true })).toBeVisible()
    await expect(page.getByText(feedback, { exact: true })).toBeVisible()
    await logout()
  })

  await test.step('Student sees the persisted grade, feedback and completed enrollment', async () => {
    await login(page, 'student')
    await navigate('Grades')
    const result = page.getByRole('article').filter({ has: page.getByRole('heading', { name: course, exact: true }) })
    await expect(result).toBeVisible()
    for (const value of ['E2E Fall 2026-2027', 'A', 'Grade: 93.5 / 100', feedback, 'Completed']) {
      await expect(result.getByText(value, { exact: true })).toBeVisible()
    }
  })
})
