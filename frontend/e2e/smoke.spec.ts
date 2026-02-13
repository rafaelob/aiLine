import { test, expect } from '@playwright/test'

/**
 * Core smoke tests for the AiLine frontend.
 * Validates that the main dashboard page loads correctly with
 * expected structure, navigation, and content.
 */
test.describe('Smoke tests', () => {
  test('dashboard page loads with welcome heading', async ({ page }) => {
    await page.goto('/pt-BR')
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toHaveText('Bem-vindo ao AiLine')
  })

  test('page title is correct', async ({ page }) => {
    await page.goto('/pt-BR')
    await expect(page).toHaveTitle('AiLine - Adaptive Inclusive Learning')
  })

  test('sidebar navigation links are present', async ({ page }) => {
    await page.goto('/pt-BR')
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav).toBeVisible()

    await expect(nav.getByText('Painel')).toBeVisible()
    await expect(nav.getByText('Planos')).toBeVisible()
    await expect(nav.getByText('Materiais')).toBeVisible()
    await expect(nav.getByText('Tutores')).toBeVisible()
    await expect(nav.getByText('Configuracoes')).toBeVisible()
  })

  test('main content area has correct landmark role', async ({ page }) => {
    await page.goto('/pt-BR')
    const main = page.locator('main#main-content')
    await expect(main).toBeVisible()
  })

  test('dashboard has quick actions section', async ({ page }) => {
    await page.goto('/pt-BR')
    const quickActionsHeading = page.getByRole('heading', { name: 'Acoes Rapidas' })
    await expect(quickActionsHeading).toBeVisible()
  })

  test('dashboard has recent plans section', async ({ page }) => {
    await page.goto('/pt-BR')
    const recentPlansHeading = page.getByRole('heading', { name: 'Planos Recentes' })
    await expect(recentPlansHeading).toBeVisible()
  })
})
