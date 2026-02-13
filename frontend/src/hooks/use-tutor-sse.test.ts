import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTutorSSE } from './use-tutor-sse'

// Mock the store
const mockAddUserMessage = vi.fn()
const mockStartStreaming = vi.fn()
const mockAppendAssistantChunk = vi.fn()
const mockFinalizeAssistant = vi.fn()
const mockSetError = vi.fn()
const mockSetSessionId = vi.fn()
const mockReset = vi.fn()

vi.mock('@/stores/tutor-store', () => ({
  useTutorStore: () => ({
    messages: [],
    isStreaming: false,
    error: null,
    sessionId: null,
    addUserMessage: mockAddUserMessage,
    startStreaming: mockStartStreaming,
    appendAssistantChunk: mockAppendAssistantChunk,
    finalizeAssistant: mockFinalizeAssistant,
    setError: mockSetError,
    setSessionId: mockSetSessionId,
    reset: mockReset,
  }),
}))

// Mock fetchEventSource
const mockFetchEventSource = vi.fn().mockResolvedValue(undefined)
vi.mock('@microsoft/fetch-event-source', () => ({
  fetchEventSource: (...args: unknown[]) => mockFetchEventSource(...args),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useTutorSSE', () => {
  it('returns expected interface shape', () => {
    const { result } = renderHook(() => useTutorSSE())

    expect(result.current).toHaveProperty('sendMessage')
    expect(result.current).toHaveProperty('cancel')
    expect(result.current).toHaveProperty('messages')
    expect(result.current).toHaveProperty('isStreaming')
    expect(result.current).toHaveProperty('error')
    expect(result.current).toHaveProperty('sessionId')
    expect(result.current).toHaveProperty('reset')
  })

  it('returns empty messages initially', () => {
    const { result } = renderHook(() => useTutorSSE())
    expect(result.current.messages).toEqual([])
  })

  it('returns isStreaming as false initially', () => {
    const { result } = renderHook(() => useTutorSSE())
    expect(result.current.isStreaming).toBe(false)
  })

  it('returns null sessionId initially', () => {
    const { result } = renderHook(() => useTutorSSE())
    expect(result.current.sessionId).toBeNull()
  })

  it('returns null error initially', () => {
    const { result } = renderHook(() => useTutorSSE())
    expect(result.current.error).toBeNull()
  })

  it('sendMessage calls addUserMessage and startStreaming', async () => {
    const { result } = renderHook(() => useTutorSSE())

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(mockAddUserMessage).toHaveBeenCalledWith('Hello')
    expect(mockStartStreaming).toHaveBeenCalled()
  })

  it('sendMessage calls fetchEventSource with correct URL', async () => {
    const { result } = renderHook(() => useTutorSSE())

    await act(async () => {
      await result.current.sendMessage('Test')
    })

    expect(mockFetchEventSource).toHaveBeenCalledWith(
      expect.stringContaining('/tutor/chat'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })

  it('cancel calls finalizeAssistant', () => {
    const { result } = renderHook(() => useTutorSSE())

    act(() => {
      result.current.cancel()
    })

    expect(mockFinalizeAssistant).toHaveBeenCalled()
  })

  it('reset is exposed from the store', () => {
    const { result } = renderHook(() => useTutorSSE())
    expect(result.current.reset).toBe(mockReset)
  })

  it('sendMessage serializes the message in the body', async () => {
    const { result } = renderHook(() => useTutorSSE())

    await act(async () => {
      await result.current.sendMessage('My question')
    })

    const callArgs = mockFetchEventSource.mock.calls[0]
    const options = callArgs[1]
    const body = JSON.parse(options.body)
    expect(body.message).toBe('My question')
  })

  it('handles fetchEventSource errors gracefully', async () => {
    mockFetchEventSource.mockRejectedValueOnce(new Error('Network failure'))

    const { result } = renderHook(() => useTutorSSE())

    await act(async () => {
      await result.current.sendMessage('Test')
    })

    expect(mockSetError).toHaveBeenCalledWith('Network failure')
  })
})
