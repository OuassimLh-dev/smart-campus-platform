import { expect } from '@playwright/test'
import type { Page } from '@playwright/test'

export async function login(page: Page, role: string) {
  await page.goto('/login')
  await page.getByLabel('Email address').fill(`${role}.e2e@example.com`)
  await page.getByLabel('Password', { exact: true }).fill('Fake-E2E-Password-Only-123!')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByRole('heading', { name: `Welcome, ${role[0].toUpperCase()}${role.slice(1)}.` })).toBeVisible()
  await expect(page.getByText(`${role}.e2e@example.com`, { exact: true })).toBeVisible()
}

