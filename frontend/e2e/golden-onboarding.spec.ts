import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Golden Path 1 -- Onboarding -> Plan Generation Wizard -> Assessment View
 *
 * Validates the critical demo flow: land on dashboard, navigate to plans,
 * fill out the 4-step wizard (subject/grade -> profile -> prompt -> review),
 * and verify the wizard advances correctly with validation.
 *
 * The wizard steps:
 *   Step 0: Disciplina + Serie/Ano -> "Proximo" button
 *   Step 1: Perfil de Acessibilidade (button grid) -> "Proximo" button
 *   Step 2: Descricao (textarea #plan-prompt) -> "Proximo" button
 *   Step 3: Revisar e Gerar -> "Gerar Plano" button
 */
test.describe('Golden Path: Onboarding -> Plan Wizard', () => {
  test('dashboard loads with welcome heading and nav', async ({ page }) => {
    await page.goto('/pt-BR')

    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toHaveText('Bem-vindo ao AiLine')

    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav).toBeVisible()
    await expect(nav.getByText('Painel')).toBeVisible()
    await expect(nav.getByText('Planos')).toBeVisible()
  })

  test('navigate to plans page via sidebar', async ({ page }) => {
    await page.goto('/pt-BR')

    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await nav.getByText('Planos').click()

    await page.waitForURL('**/pt-BR/plans')
    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()
    await expect(heading).toContainText('Planos de Estudo')
  })

  test('wizard step 0: subject and grade with validation', async ({ page }) => {
    await page.goto('/pt-BR/plans')

    // Step 0 should show subject and grade inputs
    const subjectInput = page.locator('#plan-subject')
    const gradeInput = page.locator('#plan-grade')
    await expect(subjectInput).toBeVisible()
    await expect(gradeInput).toBeVisible()

    // "Voltar" should be disabled on step 0
    await expect(page.getByRole('button', { name: 'Voltar' })).toBeDisabled()

    // Try to advance without filling -> validation errors
    await page.getByRole('button', { name: 'Proximo' }).click()
    await expect(page.getByText('Campo obrigatorio').first()).toBeVisible()

    // Fill subject and grade
    await subjectInput.fill('Ciencias')
    await gradeInput.fill('6o Ano')

    // Advance to step 1
    await page.getByRole('button', { name: 'Proximo' }).click()

    // Step 1: accessibility profile buttons should be visible
    await expect(page.getByText('Padrao')).toBeVisible()
    await expect(page.getByText('TEA (Autismo)')).toBeVisible()
  })

  test('wizard full flow through all 4 steps', async ({ page }) => {
    await page.goto('/pt-BR/plans')

    // Step 0: Subject & Grade
    await page.locator('#plan-subject').fill('Ciencias')
    await page.locator('#plan-grade').fill('6o Ano')
    await page.getByRole('button', { name: 'Proximo' }).click()

    // Step 1: Select accessibility profile (TEA)
    await expect(page.getByText('TEA (Autismo)')).toBeVisible()
    await page.getByText('TEA (Autismo)').click()
    await page.getByRole('button', { name: 'Proximo' }).click()

    // Step 2: Describe the plan
    const promptTextarea = page.locator('#plan-prompt')
    await expect(promptTextarea).toBeVisible()
    await promptTextarea.fill(
      'Plano de aula sobre fotossintese para alunos do 6o ano com adaptacoes para TEA'
    )
    await page.getByRole('button', { name: 'Proximo' }).click()

    // Step 3: Review screen
    await expect(page.getByText('Revise os dados antes de gerar')).toBeVisible()
    // Verify review shows entered data
    await expect(page.getByText('Ciencias')).toBeVisible()
    await expect(page.getByText('6o Ano', { exact: true })).toBeVisible()
    await expect(page.getByText('TEA (Autismo)')).toBeVisible()

    // The "Gerar Plano" button should be present
    await expect(page.getByRole('button', { name: 'Gerar Plano' })).toBeVisible()
  })

  test('wizard back button navigates between steps', async ({ page }) => {
    await page.goto('/pt-BR/plans')

    // Fill step 0 and advance
    await page.locator('#plan-subject').fill('Matematica')
    await page.locator('#plan-grade').fill('5o Ano')
    await page.getByRole('button', { name: 'Proximo' }).click()

    // Should be on step 1 (profiles visible)
    await expect(page.getByText('TDAH')).toBeVisible()

    // Go back to step 0
    await page.getByRole('button', { name: 'Voltar' }).click()

    // Wait for step 0 to render (animation transition)
    const subjectInput = page.locator('#plan-subject')
    await expect(subjectInput).toBeVisible({ timeout: 5_000 })

    // Data should be preserved
    await expect(subjectInput).toHaveValue('Matematica')
  })

  test('accessibility audit on dashboard page', async ({ page }) => {
    await page.goto('/pt-BR')
    await page.waitForLoadState('domcontentloaded')
    // Small delay to let client-side hydration complete
    await page.waitForTimeout(2000)

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        'Accessibility violations:',
        JSON.stringify(
          accessibilityScanResults.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            nodes: v.nodes.length,
          })),
          null,
          2
        )
      )
    }

    // Hard gate: no critical or serious violations
    const criticalOrSerious = accessibilityScanResults.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    )
    expect(criticalOrSerious).toHaveLength(0)
  })

  test('accessibility audit on plans page', async ({ page }) => {
    await page.goto('/pt-BR/plans')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        'Accessibility violations (plans):',
        JSON.stringify(
          accessibilityScanResults.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            nodes: v.nodes.length,
          })),
          null,
          2
        )
      )
    }

    const criticalOrSerious = accessibilityScanResults.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    )
    expect(criticalOrSerious).toHaveLength(0)
  })
})
