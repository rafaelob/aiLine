import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSignLanguageWorker } from './use-sign-language-worker'

// Track mock worker instances
let mockWorkerInstance: {
  postMessage: ReturnType<typeof vi.fn>
  terminate: ReturnType<typeof vi.fn>
  onmessage: ((event: MessageEvent) => void) | null
  onerror: ((event: ErrorEvent) => void) | null
}

beforeEach(() => {
  vi.clearAllMocks()

  mockWorkerInstance = {
    postMessage: vi.fn(),
    terminate: vi.fn(),
    onmessage: null,
    onerror: null,
  }

  // Mock the Worker constructor
  vi.stubGlobal('Worker', class MockWorker {
    postMessage: typeof mockWorkerInstance.postMessage
    terminate: typeof mockWorkerInstance.terminate
    onmessage: typeof mockWorkerInstance.onmessage
    onerror: typeof mockWorkerInstance.onerror

    constructor() {
      this.postMessage = mockWorkerInstance.postMessage
      this.terminate = mockWorkerInstance.terminate
      this.onmessage = null
      this.onerror = null
      // Capture handlers
      const self = this
      Object.defineProperty(mockWorkerInstance, 'onmessage', {
        get: () => self.onmessage,
        set: (fn) => { self.onmessage = fn },
        configurable: true,
      })
      Object.defineProperty(mockWorkerInstance, 'onerror', {
        get: () => self.onerror,
        set: (fn) => { self.onerror = fn },
        configurable: true,
      })
    }
  })
})

describe('useSignLanguageWorker', () => {
  it('returns expected interface shape', () => {
    const { result } = renderHook(() => useSignLanguageWorker())
    expect(result.current).toHaveProperty('ready')
    expect(result.current).toHaveProperty('error')
    expect(result.current).toHaveProperty('lastResult')
    expect(result.current).toHaveProperty('classify')
  })

  it('starts with ready=false', () => {
    const { result } = renderHook(() => useSignLanguageWorker())
    expect(result.current.ready).toBe(false)
  })

  it('starts with error=null', () => {
    const { result } = renderHook(() => useSignLanguageWorker())
    expect(result.current.error).toBeNull()
  })

  it('starts with lastResult=null', () => {
    const { result } = renderHook(() => useSignLanguageWorker())
    expect(result.current.lastResult).toBeNull()
  })

  it('sends init message to worker on mount', () => {
    renderHook(() => useSignLanguageWorker())
    expect(mockWorkerInstance.postMessage).toHaveBeenCalledWith({ type: 'init' })
  })

  it('terminates worker on unmount', () => {
    const { unmount } = renderHook(() => useSignLanguageWorker())
    unmount()
    expect(mockWorkerInstance.terminate).toHaveBeenCalled()
  })

  it('classify sends postMessage to worker', () => {
    const { result } = renderHook(() => useSignLanguageWorker())
    // ImageData is not available in jsdom, use a plain object as a stand-in
    const fakeImageData = { width: 1, height: 1, data: new Uint8ClampedArray(4) }

    act(() => {
      result.current.classify(fakeImageData as unknown as ImageData)
    })

    expect(mockWorkerInstance.postMessage).toHaveBeenCalledWith({
      type: 'classify',
      imageData: fakeImageData,
    })
  })
})
