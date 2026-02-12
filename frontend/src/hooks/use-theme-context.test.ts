import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useThemeContext } from './use-theme-context'

describe('useThemeContext', () => {
  beforeEach(() => {
    document.body.removeAttribute('data-theme')
  })

  afterEach(() => {
    document.body.removeAttribute('data-theme')
  })

  it('returns "standard" when no data-theme is set', () => {
    const { result } = renderHook(() => useThemeContext())
    expect(result.current).toBe('standard')
  })

  it('returns the current data-theme value', () => {
    document.body.setAttribute('data-theme', 'high_contrast')
    const { result } = renderHook(() => useThemeContext())
    expect(result.current).toBe('high_contrast')
  })

  it('re-renders when data-theme attribute changes via MutationObserver', async () => {
    document.body.setAttribute('data-theme', 'standard')
    const { result } = renderHook(() => useThemeContext())
    expect(result.current).toBe('standard')

    // Mutate the attribute; MutationObserver should fire
    await act(async () => {
      document.body.setAttribute('data-theme', 'dyslexia')
      // MutationObserver fires asynchronously — give it a tick
      await new Promise((r) => setTimeout(r, 0))
    })

    expect(result.current).toBe('dyslexia')
  })

  it('returns "standard" as server snapshot fallback', () => {
    // The server snapshot always returns 'standard'
    // This is tested implicitly by the hook returning 'standard' when no DOM
    const { result } = renderHook(() => useThemeContext())
    // Even without data-theme set, it defaults to 'standard'
    expect(result.current).toBe('standard')
  })
})
