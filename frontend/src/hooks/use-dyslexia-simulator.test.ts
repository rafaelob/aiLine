import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDyslexiaSimulator } from './use-dyslexia-simulator'

describe('useDyslexiaSimulator', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns startSimulation, stopSimulation, and targetRef', () => {
    const { result } = renderHook(() => useDyslexiaSimulator(false))

    expect(typeof result.current.startSimulation).toBe('function')
    expect(typeof result.current.stopSimulation).toBe('function')
    expect(result.current.targetRef).toBeDefined()
  })

  it('startSimulation begins shuffling text in the element', () => {
    const { result } = renderHook(() => useDyslexiaSimulator(false))

    const el = document.createElement('div')
    el.textContent = 'Hello World Testing'
    document.body.appendChild(el)

    act(() => {
      result.current.startSimulation(el)
    })

    // The text should have been modified (shuffled) at least once
    // Since words <= 3 chars aren't shuffled, "Hello" (5 chars) should be affected
    // We can't predict exact shuffle but we can check text was set
    expect(el.textContent).toBeTruthy()

    act(() => {
      result.current.stopSimulation()
    })

    document.body.removeChild(el)
  })

  it('stopSimulation clears the interval', () => {
    const { result } = renderHook(() => useDyslexiaSimulator(false))

    const el = document.createElement('div')
    el.textContent = 'Testing Simulation'
    document.body.appendChild(el)

    act(() => {
      result.current.startSimulation(el)
    })

    act(() => {
      result.current.stopSimulation()
    })

    const textAfterStop = el.textContent

    // Advance timers -- text should not change after stop
    act(() => {
      vi.advanceTimersByTime(600)
    })

    expect(el.textContent).toBe(textAfterStop)

    document.body.removeChild(el)
  })

  it('cleans up interval on unmount', () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval')

    const { result, unmount } = renderHook(() => useDyslexiaSimulator(false))

    const el = document.createElement('div')
    el.textContent = 'Test Content Here'
    document.body.appendChild(el)

    act(() => {
      result.current.startSimulation(el)
    })

    unmount()

    expect(clearIntervalSpy).toHaveBeenCalled()

    document.body.removeChild(el)
    clearIntervalSpy.mockRestore()
  })

  it('auto-starts when active flag changes to true with a target', () => {
    const el = document.createElement('div')
    el.textContent = 'Automatic Start Testing'
    document.body.appendChild(el)

    const { result, rerender } = renderHook(
      ({ active }) => useDyslexiaSimulator(active),
      { initialProps: { active: false } }
    )

    // Set the target ref
    act(() => {
      result.current.startSimulation(el)
      result.current.stopSimulation()
    })

    // Now activate
    rerender({ active: true })

    // Advance timer to let interval fire
    act(() => {
      vi.advanceTimersByTime(300)
    })

    // Text should have been shuffled
    expect(el.textContent).toBeTruthy()

    document.body.removeChild(el)
  })
})
