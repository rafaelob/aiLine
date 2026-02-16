import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useConfetti } from './use-confetti'

let mockReducedMotion = false

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ reducedMotion: mockReducedMotion }),
}))

const mockConfetti = vi.fn().mockResolvedValue(undefined)

vi.mock('canvas-confetti', () => ({
  default: (...args: unknown[]) => mockConfetti(...args),
}))

describe('useConfetti', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockReducedMotion = false
  })

  it('fires confetti with default origin', async () => {
    const { result } = renderHook(() => useConfetti())

    await act(async () => {
      await result.current.fire()
    })

    expect(mockConfetti).toHaveBeenCalledTimes(1)
    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({
        particleCount: 80,
        origin: { x: 0.5, y: 0.6 },
      })
    )
  })

  it('fires confetti with custom origin', async () => {
    const { result } = renderHook(() => useConfetti())

    await act(async () => {
      await result.current.fire({ x: 0.3, y: 0.4 })
    })

    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({
        origin: { x: 0.3, y: 0.4 },
      })
    )
  })

  it('does not fire when reduced motion is enabled', async () => {
    mockReducedMotion = true
    const { result } = renderHook(() => useConfetti())

    await act(async () => {
      await result.current.fire()
    })

    expect(mockConfetti).not.toHaveBeenCalled()
  })

  it('passes disableForReducedMotion flag', async () => {
    const { result } = renderHook(() => useConfetti())

    await act(async () => {
      await result.current.fire()
    })

    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({
        disableForReducedMotion: true,
      })
    )
  })
})
