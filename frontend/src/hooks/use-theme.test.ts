import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTheme } from './use-theme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.body.removeAttribute('data-theme')
  })

  it('returns "standard" as the default persona', () => {
    const { result } = renderHook(() => useTheme())
    expect(result.current.activePersona).toBe('standard')
  })

  it('applies data-theme attribute to document.body on mount', () => {
    renderHook(() => useTheme())
    expect(document.body.getAttribute('data-theme')).toBe('standard')
  })

  it('switches theme and persists to localStorage', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.switchTheme('dyslexia')
    })

    expect(document.body.getAttribute('data-theme')).toBe('dyslexia')
    expect(localStorage.getItem('ailine-persona-theme')).toBe('dyslexia')
  })

  it('reads persisted theme from localStorage on mount', () => {
    localStorage.setItem('ailine-persona-theme', 'high_contrast')

    const { result } = renderHook(() => useTheme())
    expect(result.current.activePersona).toBe('high_contrast')
  })

  it('falls back to "standard" if localStorage contains invalid persona', () => {
    localStorage.setItem('ailine-persona-theme', 'invalid_theme')

    const { result } = renderHook(() => useTheme())
    expect(result.current.activePersona).toBe('standard')
  })

  it('resets theme to "standard"', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.switchTheme('tea')
    })

    expect(result.current.activePersona).toBe('tea')

    act(() => {
      result.current.resetTheme()
    })

    expect(result.current.activePersona).toBe('standard')
    expect(document.body.getAttribute('data-theme')).toBe('standard')
  })

  it('dispatches a StorageEvent when switching theme', () => {
    const spy = vi.fn()
    window.addEventListener('storage', spy)

    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.switchTheme('motor')
    })

    expect(spy).toHaveBeenCalled()
    window.removeEventListener('storage', spy)
  })

  it('validates all 9 persona IDs as valid', () => {
    const validIds = [
      'standard', 'high_contrast', 'tea', 'tdah',
      'dyslexia', 'low_vision', 'hearing', 'motor', 'screen_reader',
    ]

    for (const id of validIds) {
      localStorage.setItem('ailine-persona-theme', id)
      const { result } = renderHook(() => useTheme())
      expect(result.current.activePersona).toBe(id)
    }
  })
})
