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
})
