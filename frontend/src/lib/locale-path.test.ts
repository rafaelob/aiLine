import { describe, it, expect } from 'vitest'
import { localePath } from './locale-path'

describe('localePath', () => {
  it('prefixes path with locale', () => {
    expect(localePath('en', '/dashboard')).toBe('/en/dashboard')
  })

  it('normalizes path without leading slash', () => {
    expect(localePath('pt-BR', 'settings')).toBe('/pt-BR/settings')
  })

  it('handles root path', () => {
    expect(localePath('es', '/')).toBe('/es/')
  })

  it('handles nested paths', () => {
    expect(localePath('en', '/app/plans/123')).toBe('/en/app/plans/123')
  })

  it('works with different locales', () => {
    expect(localePath('pt-BR', '/login')).toBe('/pt-BR/login')
    expect(localePath('es', '/login')).toBe('/es/login')
  })
})
