import { describe, it, expect, vi } from 'vitest'

// Mock next-intl/routing since it requires Next.js internals
vi.mock('next-intl/routing', () => ({
  defineRouting: (config: { locales: string[]; defaultLocale: string }) => config,
}))

import { routing, type Locale } from './routing'

describe('i18n routing configuration', () => {
  it('supports 3 locales: en, pt-BR, es', () => {
    expect(routing.locales).toEqual(['en', 'pt-BR', 'es'])
    expect(routing.locales).toHaveLength(3)
  })

  it('has pt-BR as the default locale', () => {
    expect(routing.defaultLocale).toBe('pt-BR')
  })

  it('includes English locale', () => {
    expect(routing.locales).toContain('en')
  })

  it('includes Spanish locale', () => {
    expect(routing.locales).toContain('es')
  })

  it('includes Brazilian Portuguese locale', () => {
    expect(routing.locales).toContain('pt-BR')
  })

  it('Locale type includes all supported locales', () => {
    // Type-level test: verify these assignments compile
    const en: Locale = 'en'
    const ptBR: Locale = 'pt-BR'
    const es: Locale = 'es'
    expect([en, ptBR, es]).toEqual(['en', 'pt-BR', 'es'])
  })
})
