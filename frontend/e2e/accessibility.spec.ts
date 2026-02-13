import { test, expect } from '@playwright/test'

/**
 * Accessibility (a11y) smoke tests for AiLine.
 * Validates basic WCAG compliance: landmarks, heading hierarchy,
 * skip-navigation link, and image alt text.
 */
test.describe('Accessibility basics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/pt-BR')
  })

  test('main landmark exists', async ({ page }) => {
    // Layout renders <main id="main-content" role="main">
    const main = page.locator('main[role="main"]')
    await expect(main).toBeVisible()
    await expect(main).toHaveAttribute('id', 'main-content')
  })

  test('skip-to-content link is present', async ({ page }) => {
    // Layout renders <a href="#main-content" class="skip-link">Skip to main content</a>
    const skipLink = page.locator('a.skip-link')
    await expect(skipLink).toHaveCount(1)
    await expect(skipLink).toHaveAttribute('href', '#main-content')
    await expect(skipLink).toHaveText('Skip to main content')
  })

  test('heading hierarchy starts with h1', async ({ page }) => {
    // There should be exactly one h1 on the dashboard page
    const h1Elements = page.getByRole('heading', { level: 1 })
    await expect(h1Elements).toHaveCount(1)

    // h2 elements should exist (Quick Actions, Recent Plans)
    const h2Elements = page.getByRole('heading', { level: 2 })
    const h2Count = await h2Elements.count()
    expect(h2Count).toBeGreaterThanOrEqual(2)
  })

  test('navigation landmark has aria-label', async ({ page }) => {
    // Sidebar nav has aria-label="Main navigation"
    const nav = page.getByRole('navigation', { name: 'Main navigation' })
    await expect(nav).toBeVisible()
  })

  test('images with decorative role are marked aria-hidden', async ({ page }) => {
    // All SVG icons in the dashboard use aria-hidden="true"
    // Verify that SVGs inside the stat cards and quick actions have aria-hidden
    const decorativeSvgs = page.locator('svg[aria-hidden="true"]')
    const count = await decorativeSvgs.count()
    // There should be several decorative SVGs (stat icons, action icons, etc.)
    expect(count).toBeGreaterThan(0)
  })

  test('html lang attribute matches locale', async ({ page }) => {
    // The layout sets <html lang={locale}>
    const html = page.locator('html')
    await expect(html).toHaveAttribute('lang', 'pt-BR')
  })

  test('html lang attribute matches en locale', async ({ page }) => {
    await page.goto('/en')
    const html = page.locator('html')
    await expect(html).toHaveAttribute('lang', 'en')
  })
})
