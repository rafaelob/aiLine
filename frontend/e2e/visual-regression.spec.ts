import { test, expect } from '@playwright/test'

/**
 * Visual regression tests for AiLine.
 *
 * Captures baseline screenshots of key pages under default and
 * high-contrast themes. Subsequent runs compare against baselines
 * to detect unintended visual changes.
 *
 * Baselines are stored in e2e/visual-regression.spec.ts-snapshots/
 * and should be committed to the repository.
 */

/** Helper to set a theme via the body data-theme attribute. */
async function setTheme(page: import('@playwright/test').Page, theme: string) {
  await page.evaluate(
    (t) => document.body.setAttribute('data-theme', t),
    theme
  )
  // Allow repaint after theme change
  await page.waitForTimeout(300)
}

test.describe('Visual regression - default theme', () => {
  test('dashboard page', async ({ page }) => {
    await page.goto('/pt-BR')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('dashboard-default.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('plans page', async ({ page }) => {
    await page.goto('/pt-BR/plans')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('plans-default.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('exports page', async ({ page }) => {
    await page.goto('/pt-BR/exports')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('exports-default.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('tutor chat page', async ({ page }) => {
    await page.goto('/pt-BR/tutors')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('tutors-default.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })
})

test.describe('Visual regression - high contrast theme', () => {
  test('dashboard page (high contrast)', async ({ page }) => {
    await page.goto('/pt-BR')
    await page.waitForLoadState('networkidle')
    await setTheme(page, 'high-contrast')
    await expect(page).toHaveScreenshot('dashboard-high-contrast.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('plans page (high contrast)', async ({ page }) => {
    await page.goto('/pt-BR/plans')
    await page.waitForLoadState('networkidle')
    await setTheme(page, 'high-contrast')
    await expect(page).toHaveScreenshot('plans-high-contrast.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('exports page (high contrast)', async ({ page }) => {
    await page.goto('/pt-BR/exports')
    await page.waitForLoadState('networkidle')
    await setTheme(page, 'high-contrast')
    await expect(page).toHaveScreenshot('exports-high-contrast.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })

  test('tutor chat page (high contrast)', async ({ page }) => {
    await page.goto('/pt-BR/tutors')
    await page.waitForLoadState('networkidle')
    await setTheme(page, 'high-contrast')
    await expect(page).toHaveScreenshot('tutors-high-contrast.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    })
  })
})
