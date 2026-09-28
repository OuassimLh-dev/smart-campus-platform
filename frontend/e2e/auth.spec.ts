import { expect, test } from '@playwright/test'
import { login } from './helpers'

test('login loads and invalid credentials show a useful error', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL('/login')
  await expect(page.getByLabel('Email address')).toBeVisible()
  await expect(page.getByLabel('Password', { exact: true })).toBeVisible()
  await page.getByLabel('Email address').fill('student.e2e@example.com')
  await page.getByLabel('Password', { exact: true }).fill('Definitely-wrong-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveText('The email or password is incorrect. Please try again.')
  await expect(page).toHaveURL('/login')
})

const roles = [
  { role: 'student', links: ['Profile', 'Courses', 'Enrollments', 'Grades'], blocked: ['/admin/users', '/professor/profile', '/professor/courses', '/professor/courses/1/students'] },
  { role: 'professor', links: ['Profile', 'My Courses'], blocked: ['/admin/users', '/profile', '/courses', '/enrollments', '/grades'] },
  { role: 'admin', links: ['Users', 'Departments', 'Courses', 'Academic Terms', 'Course Offerings'], blocked: ['/profile', '/courses', '/enrollments', '/grades', '/professor/profile', '/professor/courses', '/professor/courses/1/students'] },
]

for (const { role, links, blocked } of roles) {
  test(`${role} login, navigation and session restoration`, async ({ page }) => {
    await login(page, role)
    const navigation = page.getByRole('navigation', { name: 'Main navigation' })
    for (const name of links) await expect(navigation.getByRole('link', { name, exact: true })).toBeVisible()
    await page.reload()
    await expect(page.getByRole('heading', { name: /^Welcome,/ })).toBeVisible()
    if (role === 'student') {
      await navigation.getByRole('link', { name: 'Grades', exact: true }).click()
      await expect(page).toHaveURL('/grades')
      await expect(page.getByRole('heading', { name: 'My grades', exact: true })).toBeVisible()
    }
    if (role === 'admin') {
      await navigation.getByRole('link', { name: 'Users', exact: true }).click()
      await expect(page).toHaveURL('/admin/users')
      await expect(page.getByRole('heading', { name: 'Users', exact: true })).toBeVisible()
      await expect(page.getByRole('table').getByText('student.e2e@example.com', { exact: true })).toBeVisible()
    }
    await page.getByRole('button', { name: 'Log out' }).click()
    await expect(page).toHaveURL('/login')
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login')
  })
  for (const path of blocked) {
    test(`${role} cannot navigate directly to ${path}`, async ({ page }) => {
      await login(page, role)
      await page.goto(path)
      await expect(page).toHaveURL('/dashboard')
      await expect(page.getByRole('heading', { name: /^Welcome,/ })).toBeVisible()
    })
  }
}

for (const path of ['/dashboard', '/profile', '/courses', '/enrollments', '/grades', '/professor/profile', '/professor/courses', '/professor/courses/1/students', '/admin/users', '/admin/departments', '/admin/courses', '/admin/terms', '/admin/course-offerings']) {
  test(`anonymous navigation to ${path} redirects to login`, async ({ page }) => {
    await page.goto(path)
    await expect(page).toHaveURL('/login')
    await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()
  })
}
