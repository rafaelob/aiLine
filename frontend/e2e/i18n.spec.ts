import { test, expect } from '@playwright/test'

/**
 * Internationalization (i18n) tests for AiLine.
 * Validates that locale-specific routes render correct translations.
 * Supported locales: pt-BR (default), en, es.
 */
test.describe('Locale routing', () => {
  test('default locale (pt-BR) renders Portuguese text', async ({ page }) => {
    // /pt-BR is the default locale
    await page.goto('/pt-BR')
    // Dashboard heading in Portuguese
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toHaveText('Bem-vindo ao AiLine')

    // Quick actions in Portuguese
    await expect(page.getByText('Acoes Rapidas')).toBeVisible()

    // Sidebar nav items in Portuguese
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav.getByText('Painel')).toBeVisible()
  })

  test('/en route renders English text', async ({ page }) => {
    await page.goto('/en')
    // Dashboard heading in English
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toHaveText('Welcome to AiLine')

    // Quick actions in English
    await expect(page.getByText('Quick Actions')).toBeVisible()

    // Sidebar nav items in English
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav.getByText('Dashboard')).toBeVisible()
    await expect(nav.getByText('Plans')).toBeVisible()
  })

  test('/es route renders Spanish text', async ({ page }) => {
    await page.goto('/es')
    // Dashboard heading in Spanish
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toHaveText('Bienvenido a AiLine')

    // Quick actions in Spanish
    await expect(page.getByText('Acciones Rapidas')).toBeVisible()

    // Sidebar nav items in Spanish
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav.getByText('Panel')).toBeVisible()
    await expect(nav.getByText('Planes')).toBeVisible()
  })
})
