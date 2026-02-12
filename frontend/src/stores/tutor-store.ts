import { create } from 'zustand'
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

let messageCounter = 0
function nextId(): string {
  return `msg-${++messageCounter}-${Date.now()}`
}

export const useTutorStore = create<TutorState>((set) => ({
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
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + chunk }
      }
      return { messages: msgs }
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
}))
