import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChatMessage } from '@/types/tutor'

export interface TutorState {
  messages: ChatMessage[]
  sessionId: string | null
  isStreaming: boolean
  error: string | null

  addUserMessage: (content: string) => void
  startStreaming: () => void
  appendAssistantChunk: (chunk: string) => void
  finalizeAssistant: () => void
  setSessionId: (id: string) => void
  setError: (error: string) => void
  reset: () => void
}

function nextId(): string {
  return `msg-${crypto.randomUUID()}`
}

export const useTutorStore = create<TutorState>()(
  persist(
    (set) => ({
      messages: [],
      sessionId: null,
      isStreaming: false,
      error: null,

      addUserMessage: (content) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              id: nextId(),
              role: 'user',
              content,
              timestamp: new Date().toISOString(),
            },
          ],
          error: null,
        })),

      startStreaming: () =>
        set((state) => ({
          isStreaming: true,
          error: null,
          messages: [
            ...state.messages,
            {
              id: nextId(),
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
            },
          ],
        })),

      appendAssistantChunk: (chunk) =>
        set((state) => {
          const { messages } = state
          if (messages.length === 0) return state
          const last = messages[messages.length - 1]
          if (!last || last.role !== 'assistant') return state
          // Reuse head of array, only create new reference for the updated last element
          const updated = messages.slice(0, -1)
          updated.push({ ...last, content: last.content + chunk })
          return { messages: updated }
        }),

      finalizeAssistant: () => set({ isStreaming: false }),

      setSessionId: (id) => set({ sessionId: id }),

      setError: (error) => set({ error, isStreaming: false }),

      reset: () =>
        set({
          messages: [],
          sessionId: null,
          isStreaming: false,
          error: null,
        }),
    }),
    {
      name: 'ailine-tutor-chat',
      partialize: (state) => ({
        // Cap persisted messages to prevent unbounded localStorage growth
        messages: state.messages.slice(-100),
        sessionId: state.sessionId,
      }),
    },
  ),
)
