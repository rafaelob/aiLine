import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useViewTransition } from './use-view-transition'

describe('useViewTransition', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    // Clean up any startViewTransition mock
    if ('startViewTransition' in document) {
      delete (document as unknown as Record<string, unknown>).startViewTransition
    }
  })

  it('runs callback immediately when View Transitions API is unsupported', () => {
    const callback = vi.fn()
    const { result } = renderHook(() => useViewTransition())

    expect(result.current.supportsViewTransitions).toBe(false)

    act(() => {
      result.current.startTransition(callback)
    })

    expect(callback).toHaveBeenCalledOnce()
  })

  it('reports supportsViewTransitions as true when API is available', () => {
    ;(document as unknown as Record<string, unknown>).startViewTransition = vi.fn(
      (cb: () => void) => {
        cb()
        return { finished: Promise.resolve() }
      }
    )

    const { result } = renderHook(() => useViewTransition())
    expect(result.current.supportsViewTransitions).toBe(true)
  })

  it('calls startViewTransition when API is available', () => {
    const mockStartViewTransition = vi.fn((cb: () => void) => {
      cb()
      return { finished: Promise.resolve() }
    })
    ;(document as unknown as Record<string, unknown>).startViewTransition =
      mockStartViewTransition

    const callback = vi.fn()
    const { result } = renderHook(() => useViewTransition())

    act(() => {
      result.current.startTransition(callback)
    })

    expect(mockStartViewTransition).toHaveBeenCalledOnce()
    expect(callback).toHaveBeenCalledOnce()
  })

  it('sets data-vt-type and CSS variables for theme transitions', async () => {
    const mockStartViewTransition = vi.fn((cb: () => void) => {
      // Check attributes are set BEFORE callback
      expect(document.documentElement.getAttribute('data-vt-type')).toBe('theme')
      expect(document.documentElement.style.getPropertyValue('--vt-x')).toBe('100px')
      expect(document.documentElement.style.getPropertyValue('--vt-y')).toBe('200px')
      cb()
      return { finished: Promise.resolve() }
    })
    ;(document as unknown as Record<string, unknown>).startViewTransition =
      mockStartViewTransition

    const callback = vi.fn()
    const { result } = renderHook(() => useViewTransition())

    act(() => {
      result.current.startTransition(callback, { type: 'theme', x: 100, y: 200 })
    })

    expect(mockStartViewTransition).toHaveBeenCalledOnce()

    // After transition finishes, attributes should be cleaned up
    await vi.waitFor(() => {
      expect(document.documentElement.getAttribute('data-vt-type')).toBeNull()
    })
  })

  it('defaults to route transition type', () => {
    const mockStartViewTransition = vi.fn((cb: () => void) => {
      expect(document.documentElement.getAttribute('data-vt-type')).toBe('route')
      cb()
      return { finished: Promise.resolve() }
    })
    ;(document as unknown as Record<string, unknown>).startViewTransition =
      mockStartViewTransition

    const callback = vi.fn()
    const { result } = renderHook(() => useViewTransition())

    act(() => {
      result.current.startTransition(callback)
    })

    expect(mockStartViewTransition).toHaveBeenCalledOnce()
  })
})
