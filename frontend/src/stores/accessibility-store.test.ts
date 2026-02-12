import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAccessibilityStore } from './accessibility-store'

describe('accessibility-store', () => {
  beforeEach(() => {
    localStorage.clear()
    // Reset Zustand store state
    useAccessibilityStore.setState({
      theme: 'standard',
      fontSize: 'medium',
      reducedMotion: false,
      lowDistraction: false,
    })
    // Reset matchMedia mock to default (no reduced motion)
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  })

  it('has correct default state', () => {
    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('standard')
    expect(state.fontSize).toBe('medium')
    expect(state.reducedMotion).toBe(false)
  })

  it('sets theme and persists to localStorage', () => {
    useAccessibilityStore.getState().setTheme('high-contrast')

    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('high-contrast')

    const stored = JSON.parse(localStorage.getItem('ailine-a11y-prefs')!)
    expect(stored.theme).toBe('high-contrast')
  })

  it('sets fontSize and persists to localStorage', () => {
    useAccessibilityStore.getState().setFontSize('large')

    const state = useAccessibilityStore.getState()
    expect(state.fontSize).toBe('large')

    const stored = JSON.parse(localStorage.getItem('ailine-a11y-prefs')!)
    expect(stored.fontSize).toBe('large')
  })

  it('sets reducedMotion and persists to localStorage', () => {
    useAccessibilityStore.getState().setReducedMotion(true)

    const state = useAccessibilityStore.getState()
    expect(state.reducedMotion).toBe(true)

    const stored = JSON.parse(localStorage.getItem('ailine-a11y-prefs')!)
    expect(stored.reducedMotion).toBe(true)
  })

  it('hydrates from localStorage', () => {
    localStorage.setItem(
      'ailine-a11y-prefs',
      JSON.stringify({ theme: 'dyslexia', fontSize: 'xlarge', reducedMotion: true })
    )

    useAccessibilityStore.getState().hydrate()

    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('dyslexia')
    expect(state.fontSize).toBe('xlarge')
    expect(state.reducedMotion).toBe(true)
  })

  it('hydrates to defaults when localStorage is empty', () => {
    useAccessibilityStore.getState().hydrate()

    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('standard')
    expect(state.fontSize).toBe('medium')
    expect(state.reducedMotion).toBe(false)
  })

  it('hydrates to defaults when localStorage contains corrupted data', () => {
    localStorage.setItem('ailine-a11y-prefs', 'not-json')

    useAccessibilityStore.getState().hydrate()

    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('standard')
    expect(state.fontSize).toBe('medium')
    expect(state.reducedMotion).toBe(false)
  })

  it('applies data-theme to document.body on hydrate', () => {
    localStorage.setItem(
      'ailine-a11y-prefs',
      JSON.stringify({ theme: 'tea', fontSize: 'medium', reducedMotion: false })
    )

    useAccessibilityStore.getState().hydrate()

    expect(document.body.getAttribute('data-theme')).toBe('tea')
  })

  it('preserves other fields when updating a single field', () => {
    useAccessibilityStore.getState().setTheme('motor')
    useAccessibilityStore.getState().setFontSize('large')
    useAccessibilityStore.getState().setReducedMotion(true)

    const state = useAccessibilityStore.getState()
    expect(state.theme).toBe('motor')
    expect(state.fontSize).toBe('large')
    expect(state.reducedMotion).toBe(true)

    const stored = JSON.parse(localStorage.getItem('ailine-a11y-prefs')!)
    expect(stored.theme).toBe('motor')
    expect(stored.fontSize).toBe('large')
    expect(stored.reducedMotion).toBe(true)
  })

  // FINDING-19: prefers-reduced-motion integration
  it('reads reduced motion from OS media query when no stored prefs', () => {
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))

    useAccessibilityStore.getState().hydrate()

    const state = useAccessibilityStore.getState()
    expect(state.reducedMotion).toBe(true)
  })

  it('respects stored user preference over OS media query', () => {
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))

    // User explicitly stored reducedMotion: false
    localStorage.setItem(
      'ailine-a11y-prefs',
      JSON.stringify({ theme: 'standard', fontSize: 'medium', reducedMotion: false })
    )

    useAccessibilityStore.getState().hydrate()

    const state = useAccessibilityStore.getState()
    // User's explicit choice overrides OS preference
    expect(state.reducedMotion).toBe(false)
  })

  it('registers media query change listener on hydrate', () => {
    const addEventListener = vi.fn()
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener,
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))

    useAccessibilityStore.getState().hydrate()

    expect(addEventListener).toHaveBeenCalledWith('change', expect.any(Function))
  })
})
