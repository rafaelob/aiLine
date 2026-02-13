import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E configuration for AiLine frontend.
 * Runs headless Chromium against the local Next.js production build.
 *
 * Self-contained: webServer builds and starts the app automatically,
 * so no manual dev server is needed.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  timeout: 30_000,

  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  webServer: {
    command: 'pnpm build && pnpm start',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
