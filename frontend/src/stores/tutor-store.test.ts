import { describe, it, expect, beforeEach } from 'vitest'
import { useTutorStore } from './tutor-store'

beforeEach(() => {
  useTutorStore.getState().reset()
  // Clear persisted state between tests
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('ailine-tutor-chat')
  }
})

describe('useTutorStore', () => {
  it('starts with empty state', () => {
    const state = useTutorStore.getState()
    expect(state.messages).toEqual([])
    expect(state.sessionId).toBeNull()
    expect(state.isStreaming).toBe(false)
    expect(state.error).toBeNull()
  })

  it('adds user messages', () => {
    useTutorStore.getState().addUserMessage('Hello')
    const { messages } = useTutorStore.getState()
    expect(messages).toHaveLength(1)
    expect(messages[0].role).toBe('user')
    expect(messages[0].content).toBe('Hello')
  })

  it('starts streaming and adds empty assistant message', () => {
    useTutorStore.getState().startStreaming()
    const { messages, isStreaming } = useTutorStore.getState()
    expect(isStreaming).toBe(true)
    expect(messages).toHaveLength(1)
    expect(messages[0].role).toBe('assistant')
    expect(messages[0].content).toBe('')
  })

  it('appends chunks to the last assistant message', () => {
    useTutorStore.getState().startStreaming()
    useTutorStore.getState().appendAssistantChunk('Hello ')
    useTutorStore.getState().appendAssistantChunk('world')
    const { messages } = useTutorStore.getState()
    expect(messages[0].content).toBe('Hello world')
  })

  it('finalizes streaming', () => {
    useTutorStore.getState().startStreaming()
    useTutorStore.getState().finalizeAssistant()
    expect(useTutorStore.getState().isStreaming).toBe(false)
  })

  it('sets session ID', () => {
    useTutorStore.getState().setSessionId('session-123')
    expect(useTutorStore.getState().sessionId).toBe('session-123')
  })

  it('sets error and stops streaming', () => {
    useTutorStore.getState().startStreaming()
    useTutorStore.getState().setError('Connection lost')
    const state = useTutorStore.getState()
    expect(state.error).toBe('Connection lost')
    expect(state.isStreaming).toBe(false)
  })

  it('resets all state', () => {
    useTutorStore.getState().addUserMessage('Test')
    useTutorStore.getState().setSessionId('session-1')
    useTutorStore.getState().setError('Error')

    useTutorStore.getState().reset()
    const state = useTutorStore.getState()
    expect(state.messages).toEqual([])
    expect(state.sessionId).toBeNull()
    expect(state.isStreaming).toBe(false)
    expect(state.error).toBeNull()
  })

  it('clears error when adding new user message', () => {
    useTutorStore.getState().setError('Old error')
    useTutorStore.getState().addUserMessage('New message')
    expect(useTutorStore.getState().error).toBeNull()
  })

  describe('persistence', () => {
    it('persists messages and sessionId only', () => {
      useTutorStore.getState().addUserMessage('Hello')
      useTutorStore.getState().setSessionId('s-1')
      useTutorStore.getState().startStreaming()

      const stored = localStorage.getItem('ailine-tutor-chat')
      expect(stored).toBeTruthy()
      if (stored) {
        const parsed = JSON.parse(stored)
        expect(parsed.state.messages).toHaveLength(2)
        expect(parsed.state.sessionId).toBe('s-1')
        expect(parsed.state.isStreaming).toBeUndefined()
        expect(parsed.state.error).toBeUndefined()
      }
    })
  })
})
