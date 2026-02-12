import { describe, it, expect, vi } from 'vitest'

vi.mock('next-intl/middleware', () => ({
  default: vi.fn((routing) => {
    return { routing, type: 'middleware' }
  }),
}))

vi.mock('./i18n/routing', () => ({
  routing: {
    locales: ['en', 'pt-BR', 'es'],
    defaultLocale: 'pt-BR',
  },
}))

describe('proxy', () => {
  it('exports a middleware created from routing config', async () => {
    const proxyModule = await import('./proxy')
    expect(proxyModule.default).toBeDefined()
    expect(proxyModule.default).toHaveProperty('routing')
  })

  it('exports a config with matcher pattern', async () => {
    const proxyModule = await import('./proxy')
    expect(proxyModule.config).toBeDefined()
    expect(proxyModule.config.matcher).toBeDefined()
    expect(typeof proxyModule.config.matcher).toBe('string')
  })

  it('matcher excludes api, _next, and static files', async () => {
    const proxyModule = await import('./proxy')
    const matcher = proxyModule.config.matcher
    expect(matcher).toContain('api')
    expect(matcher).toContain('_next')
  })
})
