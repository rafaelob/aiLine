import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useVoiceInput } from './use-voice-input'

const mockStart = vi.fn()
const mockStop = vi.fn()
const mockAbort = vi.fn()

class MockSpeechRecognition {
  lang = ''
  interimResults = false
  continuous = false
  onresult: ((event: unknown) => void) | null = null
  onerror: ((event: unknown) => void) | null = null
  onend: (() => void) | null = null

  start() {
    mockStart()
  }
  stop() {
    mockStop()
    this.onend?.()
  }
  abort() {
    mockAbort()
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  // Set up WebSpeech API on window
  Object.defineProperty(window, 'SpeechRecognition', {
    value: MockSpeechRecognition,
    writable: true,
    configurable: true,
  })
})

describe('useVoiceInput', () => {
  it('reports isSupported as true when SpeechRecognition available', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(true)
  })

  it('sets error when SpeechRecognition not available', () => {
    // Temporarily remove SpeechRecognition
    const orig = (window as unknown as Record<string, unknown>).SpeechRecognition
    ;(window as unknown as Record<string, unknown>).SpeechRecognition = undefined
    ;(window as unknown as Record<string, unknown>).webkitSpeechRecognition = undefined

    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    expect(result.current.error).toBe('speech_not_supported')
    expect(result.current.isListening).toBe(false)

    // Restore
    ;(window as unknown as Record<string, unknown>).SpeechRecognition = orig
  })

  it('starts listening when startListening called', () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    expect(result.current.isListening).toBe(true)
    expect(mockStart).toHaveBeenCalled()
  })

  it('stops listening when stopListening called', () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    act(() => {
      result.current.stopListening()
    })

    expect(result.current.isListening).toBe(false)
  })

  it('starts with empty transcript', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.transcript).toBe('')
  })

  it('starts with no error', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.error).toBeNull()
  })
})
