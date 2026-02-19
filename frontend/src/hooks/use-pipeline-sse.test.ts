import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'

// Hoist mock data so vi.mock factories can reference them
const { mockFetchEventSource, mockStoreState } = vi.hoisted(() => {
  const mockFetchEventSource = vi.fn()
  const mockStoreState = {
    runId: null as string | null,
    currentStage: null as string | null,
    stages: [] as unknown[],
    events: [] as unknown[],
    plan: null,
    qualityReport: null,
    score: null,
    scorecard: null,
    isRunning: false,
    error: null as string | null,
    startRun: vi.fn(),
    addEvent: vi.fn(),
    setPlan: vi.fn(),
    setQualityReport: vi.fn(),
    setScore: vi.fn(),
    setScorecard: vi.fn(),
    setError: vi.fn(),
    reset: vi.fn(),
  }
  return { mockFetchEventSource, mockStoreState }
})

vi.mock('@microsoft/fetch-event-source', () => ({
  fetchEventSource: (...args: unknown[]) => mockFetchEventSource(...args),
}))

vi.mock('@/stores/pipeline-store', () => {
  const fn = () => mockStoreState
  fn.getState = () => mockStoreState
  return { usePipelineStore: fn }
})

// Import after mocks
import { usePipelineSSE } from './use-pipeline-sse'

describe('usePipelineSSE', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStoreState.runId = null
    mockStoreState.isRunning = false
    mockStoreState.error = null
    mockStoreState.plan = null
    mockFetchEventSource.mockResolvedValue(undefined)
  })

  it('returns the correct interface shape', () => {
    const { result } = renderHook(() => usePipelineSSE())

    expect(result.current).toHaveProperty('startGeneration')
    expect(result.current).toHaveProperty('cancel')
    expect(result.current).toHaveProperty('runId')
    expect(result.current).toHaveProperty('stages')
    expect(result.current).toHaveProperty('events')
    expect(result.current).toHaveProperty('currentStage')
    expect(result.current).toHaveProperty('plan')
    expect(result.current).toHaveProperty('qualityReport')
    expect(result.current).toHaveProperty('score')
    expect(result.current).toHaveProperty('isRunning')
    expect(result.current).toHaveProperty('error')
    expect(typeof result.current.startGeneration).toBe('function')
    expect(typeof result.current.cancel).toBe('function')
  })

  it('calls store.reset and fetchEventSource on startGeneration', async () => {
    const { result } = renderHook(() => usePipelineSSE())

    await act(async () => {
      await result.current.startGeneration({
        prompt: 'Test plan',
        grade: '5th',
        subject: 'Math',
        accessibility_profile: 'standard',
        locale: 'pt-BR',
      })
    })

    expect(mockStoreState.reset).toHaveBeenCalled()
    expect(mockFetchEventSource).toHaveBeenCalledTimes(1)

    const callArgs = mockFetchEventSource.mock.calls[0]
    expect(callArgs[0]).toContain('/plans/generate/stream')
    expect(callArgs[1].method).toBe('POST')
    expect(callArgs[1].headers['Content-Type']).toBe('application/json')
  })

  it('sends the request body as JSON', async () => {
    const { result } = renderHook(() => usePipelineSSE())
    const request = {
      prompt: 'Test plan',
      grade: '5th',
      subject: 'Math',
      accessibility_profile: 'tea',
      locale: 'pt-BR',
    }

    await act(async () => {
      await result.current.startGeneration(request)
    })

    const callArgs = mockFetchEventSource.mock.calls[0]
    expect(JSON.parse(callArgs[1].body)).toEqual(request)
  })

  it('calls store.setError on cancel', () => {
    const { result } = renderHook(() => usePipelineSSE())

    act(() => {
      result.current.cancel()
    })

    expect(mockStoreState.setError).toHaveBeenCalledWith('Generation cancelled')
  })

  it('processes run.started events through onmessage', async () => {
    mockFetchEventSource.mockImplementation(async (_url: string, options: Record<string, unknown>) => {
      const onmessage = options.onmessage as (msg: { data: string }) => void
      onmessage({
        data: JSON.stringify({
          type: 'run.started',
          run_id: 'test-run-123',
          seq: 0,
          ts: new Date().toISOString(),
          stage: null,
          payload: {},
        }),
      })
    })

    const { result } = renderHook(() => usePipelineSSE())

    await act(async () => {
      await result.current.startGeneration({
        prompt: 'Test',
        grade: '5th',
        subject: 'Math',
        accessibility_profile: 'standard',
        locale: 'pt-BR',
      })
    })

    expect(mockStoreState.startRun).toHaveBeenCalledWith('test-run-123')
    expect(mockStoreState.addEvent).toHaveBeenCalled()
  })

  it('handles connection errors gracefully', async () => {
    mockFetchEventSource.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => usePipelineSSE())

    await act(async () => {
      await result.current.startGeneration({
        prompt: 'Test',
        grade: '5th',
        subject: 'Math',
        accessibility_profile: 'standard',
        locale: 'pt-BR',
      })
    })

    expect(mockStoreState.setError).toHaveBeenCalledWith('Network error')
  })

  it('skips messages with empty data', async () => {
    mockFetchEventSource.mockImplementation(async (_url: string, options: Record<string, unknown>) => {
      const onmessage = options.onmessage as (msg: { data: string }) => void
      onmessage({ data: '' })
    })

    const { result } = renderHook(() => usePipelineSSE())

    await act(async () => {
      await result.current.startGeneration({
        prompt: 'Test',
        grade: '5th',
        subject: 'Math',
        accessibility_profile: 'standard',
        locale: 'pt-BR',
      })
    })

    expect(mockStoreState.addEvent).not.toHaveBeenCalled()
  })
})
