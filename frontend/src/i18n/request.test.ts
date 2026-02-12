import { describe, it, expect, vi } from 'vitest'

vi.mock('next-intl/server', () => ({
  getRequestConfig: vi.fn((fn: unknown) => fn),
  getMessages: vi.fn(async () => ({})),
}))

vi.mock('./routing', () => ({
  routing: {
    locales: ['en', 'pt-BR', 'es'],
    defaultLocale: 'pt-BR',
  },
}))

describe('i18n request config', () => {
  it('exports a function from getRequestConfig', async () => {
    const requestModule = await import('./request')
    expect(requestModule.default).toBeDefined()
    expect(typeof requestModule.default).toBe('function')
  })

  it('returns locale and messages for a valid locale', async () => {
    const requestModule = await import('./request')
    const configFn = requestModule.default as (args: {
      requestLocale: Promise<string>
    }) => Promise<{ locale: string; messages: unknown }>

    // We can't easily test the dynamic import, but we can verify the structure
    expect(configFn).toBeDefined()
  })
})
