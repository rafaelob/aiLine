import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLibrasCaptioning } from './use-libras-captioning'

// Track mock worker instance
let mockWorkerInstance: {
  postMessage: ReturnType<typeof vi.fn>
  terminate: ReturnType<typeof vi.fn>
  onmessage: ((event: MessageEvent) => void) | null
}

// Track WebSocket mock
let mockWsInstance: {
  send: ReturnType<typeof vi.fn>
  close: ReturnType<typeof vi.fn>
  readyState: number
  onopen: (() => void) | null
  onmessage: ((event: MessageEvent) => void) | null
  onerror: (() => void) | null
  onclose: (() => void) | null
}

beforeEach(() => {
  vi.clearAllMocks()

  mockWorkerInstance = {
    postMessage: vi.fn(),
    terminate: vi.fn(),
    onmessage: null,
  }

  // Mock Worker
  vi.stubGlobal('Worker', class MockWorker {
    postMessage: typeof mockWorkerInstance.postMessage
    terminate: typeof mockWorkerInstance.terminate
    onmessage: typeof mockWorkerInstance.onmessage
    onerror: (() => void) | null

    constructor() {
      this.postMessage = mockWorkerInstance.postMessage
      this.terminate = mockWorkerInstance.terminate
      this.onmessage = null
      this.onerror = null
      const self = this // eslint-disable-line @typescript-eslint/no-this-alias
      Object.defineProperty(mockWorkerInstance, 'onmessage', {
        get: () => self.onmessage,
        set: (fn) => { self.onmessage = fn },
        configurable: true,
      })
    }
  })

  mockWsInstance = {
    send: vi.fn(),
    close: vi.fn(),
    readyState: 1, // OPEN
    onopen: null,
    onmessage: null,
    onerror: null,
    onclose: null,
  }

  // Mock WebSocket
  vi.stubGlobal('WebSocket', class MockWebSocket {
    static OPEN = 1

    send = mockWsInstance.send
    close = mockWsInstance.close
    readyState = mockWsInstance.readyState

    set onopen(fn: (() => void) | null) { mockWsInstance.onopen = fn }
    get onopen() { return mockWsInstance.onopen }
    set onmessage(fn: ((event: MessageEvent) => void) | null) { mockWsInstance.onmessage = fn }
    get onmessage() { return mockWsInstance.onmessage }
    set onerror(fn: (() => void) | null) { mockWsInstance.onerror = fn }
    get onerror() { return mockWsInstance.onerror }
    set onclose(fn: (() => void) | null) { mockWsInstance.onclose = fn }
    get onclose() { return mockWsInstance.onclose }

    constructor() {}
  })
})

describe('useLibrasCaptioning', () => {
  it('returns expected interface shape', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current).toHaveProperty('isRecording')
    expect(result.current).toHaveProperty('rawGlosses')
    expect(result.current).toHaveProperty('draftText')
    expect(result.current).toHaveProperty('committedText')
    expect(result.current).toHaveProperty('confidence')
    expect(result.current).toHaveProperty('connectionStatus')
    expect(result.current).toHaveProperty('error')
    expect(result.current).toHaveProperty('startCaptioning')
    expect(result.current).toHaveProperty('stopCaptioning')
    expect(result.current).toHaveProperty('feedLandmarks')
  })

  it('starts not recording', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.isRecording).toBe(false)
  })

  it('starts with disconnected status', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.connectionStatus).toBe('disconnected')
  })

  it('starts with empty glosses', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.rawGlosses).toEqual([])
  })

  it('starts with empty text', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.draftText).toBe('')
    expect(result.current.committedText).toBe('')
  })

  it('starts with zero confidence', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.confidence).toBe(0)
  })

  it('starts with null error', () => {
    const { result } = renderHook(() => useLibrasCaptioning())
    expect(result.current.error).toBeNull()
  })

  it('initializes the inference worker on mount', () => {
    renderHook(() => useLibrasCaptioning())
    expect(mockWorkerInstance.postMessage).toHaveBeenCalledWith({ type: 'init' })
  })

  it('terminates worker on unmount', () => {
    const { unmount } = renderHook(() => useLibrasCaptioning())
    unmount()
    expect(mockWorkerInstance.terminate).toHaveBeenCalled()
  })

  it('startCaptioning sets isRecording to true', () => {
    const { result } = renderHook(() => useLibrasCaptioning())

    act(() => {
      result.current.startCaptioning()
    })

    expect(result.current.isRecording).toBe(true)
  })

  it('stopCaptioning sets isRecording to false', () => {
    const { result } = renderHook(() => useLibrasCaptioning())

    act(() => {
      result.current.startCaptioning()
    })

    act(() => {
      result.current.stopCaptioning()
    })

    expect(result.current.isRecording).toBe(false)
  })

  it('startCaptioning clears error and previous state', () => {
    const { result } = renderHook(() => useLibrasCaptioning())

    act(() => {
      result.current.startCaptioning()
    })

    expect(result.current.error).toBeNull()
    expect(result.current.rawGlosses).toEqual([])
    expect(result.current.draftText).toBe('')
    expect(result.current.committedText).toBe('')
  })

  it('feedLandmarks does nothing when not recording', () => {
    const { result } = renderHook(() => useLibrasCaptioning())

    act(() => {
      result.current.feedLandmarks([0.1, 0.2, 0.3])
    })

    // Should not crash or send anything beyond init
    expect(mockWorkerInstance.postMessage).toHaveBeenCalledTimes(1) // Only init
  })
})
