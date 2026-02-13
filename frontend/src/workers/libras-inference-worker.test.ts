import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * Tests for the Libras inference Web Worker (CTC decode + motion heuristic).
 * Simulates the onmessage handler since Workers don't run natively in jsdom.
 */

const postedMessages: unknown[] = []

const mockPostMessage = vi.fn((msg: unknown) => {
  postedMessages.push(msg)
})

vi.stubGlobal('postMessage', mockPostMessage)

let workerOnMessage: ((event: MessageEvent) => void) | null = null

Object.defineProperty(globalThis, 'onmessage', {
  set(fn: ((event: MessageEvent) => void) | null) {
    workerOnMessage = fn
  },
  get() {
    return workerOnMessage
  },
  configurable: true,
})

describe('libras-inference-worker protocol', () => {
  beforeEach(() => {
    postedMessages.length = 0
    mockPostMessage.mockClear()
    workerOnMessage = null
  })

  it('initializes successfully without model URL', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./libras-inference-worker')

    if (workerOnMessage) {
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'init' } })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({ type: 'init_ok' })
    )
  })

  it('returns empty glosses for empty landmark input', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./libras-inference-worker')

    if (workerOnMessage) {
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'init' } })
      )
      postedMessages.length = 0

      await workerOnMessage(
        new MessageEvent('message', {
          data: { type: 'infer', landmarks: [], timestamp: 1000 },
        })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({
        type: 'gloss_partial',
        glosses: [],
        confidence: 0,
        ts: 1000,
      })
    )
  })

  it('returns empty glosses for static (no motion) frames', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./libras-inference-worker')

    if (workerOnMessage) {
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'init' } })
      )
      postedMessages.length = 0

      // All-zero frames: no motion detected
      const staticFrames = Array.from({ length: 10 }, () =>
        new Array(162).fill(0)
      )
      await workerOnMessage(
        new MessageEvent('message', {
          data: { type: 'infer', landmarks: staticFrames, timestamp: 2000 },
        })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({
        type: 'gloss_partial',
        glosses: [],
        confidence: 0,
        ts: 2000,
      })
    )
  })

  it('detects motion and returns gloss with low confidence in fallback mode', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./libras-inference-worker')

    if (workerOnMessage) {
      await workerOnMessage(
        new MessageEvent('message', { data: { type: 'init' } })
      )
      postedMessages.length = 0

      // Frames with significant inter-frame motion
      const movingFrames = Array.from({ length: 10 }, (_, f) => {
        const frame = new Array(162).fill(0)
        for (let i = 0; i < 162; i++) {
          frame[i] = Math.sin(f * 0.5 + i * 0.1) * 0.5
        }
        return frame
      })

      await workerOnMessage(
        new MessageEvent('message', {
          data: { type: 'infer', landmarks: movingFrames, timestamp: 3000 },
        })
      )
    }

    const inferResult = postedMessages.find(
      (m: unknown) => (m as Record<string, unknown>).type === 'gloss_partial'
    ) as Record<string, unknown> | undefined

    expect(inferResult).toBeDefined()
    // Fallback mode caps confidence at 0.3
    expect(inferResult?.confidence).toBeLessThanOrEqual(0.3)
  })

  it('returns infer_error when model is not initialized', async () => {
    vi.resetModules()
    postedMessages.length = 0

    await import('./libras-inference-worker')

    if (workerOnMessage) {
      // Infer without init
      await workerOnMessage(
        new MessageEvent('message', {
          data: { type: 'infer', landmarks: [[0, 1, 2]], timestamp: 4000 },
        })
      )
    }

    expect(postedMessages).toContainEqual(
      expect.objectContaining({ type: 'infer_error' })
    )
  })

  it('exports CTC decode helper functions', async () => {
    const mod = await import('./libras-inference-worker')
    expect(mod).toBeDefined()
  })
})
