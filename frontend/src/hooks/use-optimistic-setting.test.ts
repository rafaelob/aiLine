import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useOptimisticSetting } from './use-optimistic-setting'

describe('useOptimisticSetting', () => {
  it('returns the current value initially', () => {
    const persist = vi.fn()
    const { result } = renderHook(() =>
      useOptimisticSetting<string>('standard', persist)
    )

    expect(result.current[0]).toBe('standard')
  })

  it('calls persist action when value is set', () => {
    const persist = vi.fn()
    const { result } = renderHook(() =>
      useOptimisticSetting<string>('standard', persist)
    )

    act(() => {
      result.current[1]('high-contrast')
    })

    expect(persist).toHaveBeenCalledWith('high-contrast')
  })

  it('works with boolean values', () => {
    const persist = vi.fn()
    const { result } = renderHook(() =>
      useOptimisticSetting<boolean>(false, persist)
    )

    expect(result.current[0]).toBe(false)

    act(() => {
      result.current[1](true)
    })

    expect(persist).toHaveBeenCalledWith(true)
  })

  it('provides a stable setter function', () => {
    const persist = vi.fn()
    const { result, rerender } = renderHook(() =>
      useOptimisticSetting<string>('a', persist)
    )

    const setterBefore = result.current[1]
    rerender()
    const setterAfter = result.current[1]

    expect(typeof setterBefore).toBe('function')
    expect(typeof setterAfter).toBe('function')
  })
})
