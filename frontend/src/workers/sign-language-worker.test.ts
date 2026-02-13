import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * Tests for the sign language Web Worker communication protocol (FINDING-24).
 * Since Workers don't run natively in jsdom, we test the message protocol
 * by simulating the onmessage handler.
 */

// Capture posted messages
const postedMessages: unknown[] = []

// Mock DedicatedWorkerGlobalScope
const mockPostMessage = vi.fn((msg: unknown) => {
  postedMessages.push(msg)
})

// Set up the global scope mock before importing the worker module
vi.stubGlobal('postMessage', mockPostMessage)

// Simulate the worker's onmessage being set
let workerOnMessage: ((event: MessageEvent) => void) | null = null

const _originalDefineProperty = Object.defineProperty
Object.defineProperty(globalThis, 'onmessage', {
  set(fn: ((event: MessageEvent) => void) | null) {
    workerOnMessage = fn
  },
  get() {
    return workerOnMessage
  },
  configurable: true,
})

describe('sign-language-worker protocol', () => {
  beforeEach(() => {
    postedMessages.length = 0
    mockPostMessage.mockClear()
    workerOnMessage = null
  })

  it('exports correct message types', async () => {
    const mod = await import('./sign-language-worker')
    // Module should have type exports (WorkerInMessage, WorkerOutMessage)
    // Just verify the module loads without error
    expect(mod).toBeDefined()
  })

  it('defines WorkerInMessage and WorkerOutMessage types', async () => {
    // Type-level test: verify the types compile correctly
    const initMsg: import('./sign-language-worker').WorkerInMessage = { type: 'init' }
    expect(initMsg.type).toBe('init')

    // ImageData not available in jsdom — use a mock object for type checking
    const mockImageData = { width: 1, height: 1, data: new Uint8ClampedArray(4) } as unknown as ImageData
    const classifyMsg: import('./sign-language-worker').WorkerInMessage = {
      type: 'classify',
      imageData: mockImageData,
    }
    expect(classifyMsg.type).toBe('classify')
  })

  it('handles init message and responds with init_ok', async () => {
    // Re-import to trigger the onmessage setup
    vi.resetModules()
    postedMessages.length = 0

    await import('./sign-language-worker')

    if (workerOnMessage) {
      await workerOnMessage(new MessageEvent('message', { data: { type: 'init' } }))
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({ type: 'init_ok' })
    )
  })

  it('handles classify message after initialization (fallback mode)', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./sign-language-worker')

    if (workerOnMessage) {
      // First init
      await workerOnMessage(new MessageEvent('message', { data: { type: 'init' } }))
      postedMessages.length = 0

      // Then classify (ImageData not available in jsdom — use mock)
      const imageData = { width: 2, height: 2, data: new Uint8ClampedArray(16) } as unknown as ImageData
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'classify', imageData } })
      )
    }

    // Without NEXT_PUBLIC_SIGN_RECOGNITION_ENABLED, returns 'experimental'
    expect(postedMessages).toContainEqual(
      expect.objectContaining({
        type: 'result',
        gesture: 'experimental',
        confidence: 0,
      })
    )
  })

  it('handles extract_landmarks message after initialization', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./sign-language-worker')

    if (workerOnMessage) {
      await workerOnMessage(new MessageEvent('message', { data: { type: 'init' } }))
      postedMessages.length = 0

      const imageData = { width: 2, height: 2, data: new Uint8ClampedArray(16) } as unknown as ImageData
      await workerOnMessage(
        new MessageEvent('message', {
          data: { type: 'extract_landmarks', imageData, timestamp: 12345 },
        })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({
        type: 'landmarks',
        landmarks: expect.any(Array),
        timestamp: 12345,
      })
    )
  })

  it('returns classify_error when models are not initialized', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./sign-language-worker')

    if (workerOnMessage) {
      // Classify without init (ImageData not available in jsdom — use mock)
      const imageData = { width: 2, height: 2, data: new Uint8ClampedArray(16) } as unknown as ImageData
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'classify', imageData } })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({ type: 'classify_error' })
    )
  })
})
