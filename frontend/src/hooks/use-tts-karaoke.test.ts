import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTTSKaraoke } from './use-tts-karaoke'

const mockSpeak = vi.fn()
const mockCancel = vi.fn()
const mockPause = vi.fn()
const mockResume = vi.fn()

interface MockUtterance {
  text: string
  lang: string
  rate: number
  onboundary: ((e: unknown) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
}

let lastUtterance: MockUtterance | null = null

function MockSpeechSynthesisUtterance(text: string) {
  const instance: MockUtterance = {
    text,
    lang: '',
    rate: 1,
    onboundary: null,
    onend: null,
    onerror: null,
  }
  lastUtterance = instance
  return instance
}

beforeEach(() => {
  vi.clearAllMocks()
  lastUtterance = null

  Object.defineProperty(window, 'speechSynthesis', {
    value: {
      speak: mockSpeak,
      cancel: mockCancel,
      pause: mockPause,
      resume: mockResume,
    },
    writable: true,
    configurable: true,
  })

  Object.defineProperty(window, 'SpeechSynthesisUtterance', {
    value: MockSpeechSynthesisUtterance,
    writable: true,
    configurable: true,
  })
})

describe('useTTSKaraoke', () => {
  it('starts with isPlaying false and currentWordIndex -1', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    expect(result.current.isPlaying).toBe(false)
    expect(result.current.currentWordIndex).toBe(-1)
    expect(result.current.speed).toBe(1)
  })

  it('speak sets isPlaying to true and calls speechSynthesis.speak', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Hello world')
    })
    expect(mockCancel).toHaveBeenCalled()
    expect(mockSpeak).toHaveBeenCalled()
    expect(result.current.isPlaying).toBe(true)
    expect(result.current.currentWordIndex).toBe(0)
  })

  it('stop cancels and resets state', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Hello world')
    })
    act(() => {
      result.current.stop()
    })
    expect(mockCancel).toHaveBeenCalledTimes(2) // once in speak, once in stop
    expect(result.current.isPlaying).toBe(false)
    expect(result.current.currentWordIndex).toBe(-1)
  })

  it('pause calls speechSynthesis.pause', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Hello world')
    })
    act(() => {
      result.current.pause()
    })
    expect(mockPause).toHaveBeenCalled()
    expect(result.current.isPlaying).toBe(false)
  })

  it('resume calls speechSynthesis.resume', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.resume()
    })
    expect(mockResume).toHaveBeenCalled()
    expect(result.current.isPlaying).toBe(true)
  })

  it('setSpeed updates speed', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.setSpeed(1.5)
    })
    expect(result.current.speed).toBe(1.5)
  })

  it('onend callback resets state', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Hello world')
    })
    expect(lastUtterance).not.toBeNull()
    act(() => {
      lastUtterance?.onend?.()
    })
    expect(result.current.isPlaying).toBe(false)
    expect(result.current.currentWordIndex).toBe(-1)
  })

  it('onboundary updates currentWordIndex', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Hello world test')
    })
    // Simulate word boundary at charIndex 6 (start of "world")
    act(() => {
      lastUtterance?.onboundary?.({ name: 'word', charIndex: 6 })
    })
    expect(result.current.currentWordIndex).toBe(1)
  })

  it('sets pt-BR as default lang', () => {
    const { result } = renderHook(() => useTTSKaraoke())
    act(() => {
      result.current.speak('Ola mundo')
    })
    expect(lastUtterance?.lang).toBe('pt-BR')
  })
})
