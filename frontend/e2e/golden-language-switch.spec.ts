import { test, expect } from '@playwright/test'

/**
 * Golden Path 2 -- Language switch mid-session (PT-BR -> EN -> ES)
 *
 * Validates that the locale switcher in the top bar correctly updates
 * all UI text in real-time, preserves the current page context,
 * and renders correct translations for each locale.
 */
test.describe('Golden Path: Language Switch Mid-Session', () => {
  test('locale switcher is visible and defaults to pt-BR', async ({ page }) => {
    await page.goto('/pt-BR')

    const localeSelect = page.locator('#locale-select')
    await expect(localeSelect).toBeVisible()
    await expect(localeSelect).toHaveValue('pt-BR')
  })

  test('switch from PT-BR to EN updates dashboard text', async ({ page }) => {
    await page.goto('/pt-BR')

    // Verify PT-BR content first
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Bem-vindo ao AiLine')
    await expect(page.getByText('Acoes Rapidas')).toBeVisible()

    // Switch to English
    await page.locator('#locale-select').selectOption('en')
    await page.waitForURL('**/en')

    // Verify English content
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Welcome to AiLine')
    await expect(page.getByText('Quick Actions')).toBeVisible()

    // Sidebar should also be in English
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav.getByText('Dashboard')).toBeVisible()
    await expect(nav.getByText('Plans')).toBeVisible()
  })

  test('switch from EN to ES updates dashboard text', async ({ page }) => {
    await page.goto('/en')

    // Verify English first
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Welcome to AiLine')

    // Switch to Spanish
    await page.locator('#locale-select').selectOption('es')
    await page.waitForURL('**/es')

    // Verify Spanish content
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Bienvenido a AiLine')
    await expect(page.getByText('Acciones Rapidas')).toBeVisible()

    // Sidebar in Spanish
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav.getByText('Panel')).toBeVisible()
    await expect(nav.getByText('Planes')).toBeVisible()
  })

  test('full round-trip: PT-BR -> EN -> ES -> PT-BR', async ({ page }) => {
    test.setTimeout(60_000)
    await page.goto('/pt-BR')

    // Verify PT-BR
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Bem-vindo ao AiLine')

    // Switch to EN
    await page.locator('#locale-select').selectOption('en')
    await page.waitForURL('**/en', { timeout: 15_000 })
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Welcome to AiLine')

    // Switch to ES
    await page.locator('#locale-select').selectOption('es')
    await page.waitForURL('**/es', { timeout: 15_000 })
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Bienvenido a AiLine')

    // Switch back to PT-BR
    await page.locator('#locale-select').selectOption('pt-BR')
    await page.waitForURL('**/pt-BR', { timeout: 15_000 })
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Bem-vindo ao AiLine')
  })

  test('language switch preserves page context on plans page', async ({ page }) => {
    await page.goto('/pt-BR/plans')

    // Verify PT-BR on plans page
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Planos de Estudo')

    // Switch to EN while on plans page
    await page.locator('#locale-select').selectOption('en')
    await page.waitForURL('**/en/plans')

    // Should still be on plans page, but in English
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Study Plans')

    // Switch to ES
    await page.locator('#locale-select').selectOption('es')
    await page.waitForURL('**/es/plans')

    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Planes de Estudio')
  })

  test('html lang attribute updates on locale switch', async ({ page }) => {
    await page.goto('/pt-BR')
    await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR')

    await page.locator('#locale-select').selectOption('en')
    await page.waitForURL('**/en')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')

    await page.locator('#locale-select').selectOption('es')
    await page.waitForURL('**/es')
    await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  })
})
