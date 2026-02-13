import { test, expect } from '@playwright/test'

/**
 * Error handling tests for AiLine.
 * Validates that unknown routes show the 404 page with correct
 * content and a link back to the home page.
 */
test.describe('Error handling', () => {
  test('404 page renders for unknown routes', async ({ page }) => {
    // Navigate to a route that does not exist under the pt-BR locale
    await page.goto('/pt-BR/this-page-does-not-exist')

    // The not-found page displays "404" in a badge element
    await expect(page.getByText('404')).toBeVisible()

    // The not-found heading uses the 'not_found_title' translation
    // pt-BR: "Pagina nao encontrada"
    await expect(page.getByRole('heading', { name: 'Pagina nao encontrada' })).toBeVisible()

    // The description text should be visible
    await expect(
      page.getByText('A pagina que voce procura nao existe ou foi movida.')
    ).toBeVisible()
  })

  test('404 page has "go to home" link', async ({ page }) => {
    await page.goto('/pt-BR/nonexistent-route')

    // The not-found page has a link to go home
    // pt-BR: "Ir para o inicio"
    const homeLink = page.getByRole('link', { name: 'Ir para o inicio' })
    await expect(homeLink).toBeVisible()
    await expect(homeLink).toHaveAttribute('href', '/')
  })

  test('404 page renders in English for /en locale', async ({ page }) => {
    await page.goto('/en/does-not-exist')

    await expect(page.getByText('404')).toBeVisible()
    // en: "Page not found"
    await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible()

    // en: "Go to home"
    const homeLink = page.getByRole('link', { name: 'Go to home' })
    await expect(homeLink).toBeVisible()
  })
})
