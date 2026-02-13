import { test, expect } from '@playwright/test'

/**
 * Error handling tests for AiLine.
 * Validates that unknown routes show a 404 page.
 * Next.js 16 renders its default not-found page for unknown routes.
 */
test.describe('Error handling', () => {
  test('404 page renders for unknown routes', async ({ page }) => {
    await page.goto('/pt-BR/this-page-does-not-exist')

    // Next.js renders a 404 heading
    await expect(page.getByText('404')).toBeVisible()
  })

  test('404 page for English locale', async ({ page }) => {
    await page.goto('/en/does-not-exist')

    await expect(page.getByText('404')).toBeVisible()
  })
})
