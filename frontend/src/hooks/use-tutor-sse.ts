'use client'

import { useCallback, useRef, useEffect } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { useTutorStore } from '@/stores/tutor-store'
import { API_BASE, getAuthHeaders } from '@/lib/api'

/**
 * SSE hook for tutor chat streaming.
 * Sends a message and streams back the AI response token-by-token.
 */
export function useTutorSSE() {
  const abortRef = useRef<AbortController | null>(null)
  const store = useTutorStore()

  // Abort SSE connection on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const sendMessage = useCallback(
    async (message: string) => {
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      store.addUserMessage(message)
      store.startStreaming()

      try {
        await fetchEventSource(`${API_BASE}/tutor/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
            ...getAuthHeaders(),
          },
          body: JSON.stringify({
            message,
            session_id: store.sessionId,
          }),
          signal: ctrl.signal,

          onopen: async (response) => {
            if (!response.ok) {
              throw new Error(
                `Tutor SSE failed: ${response.status} ${response.statusText}`
              )
            }
          },

          onmessage: (msg) => {
            if (!msg.data) return
            try {
              const data = JSON.parse(msg.data)

              if (data.session_id && !store.sessionId) {
                store.setSessionId(data.session_id)
              }

              if (data.chunk) {
                store.appendAssistantChunk(data.chunk)
              }

              if (data.done) {
                store.finalizeAssistant()
              }
            } catch {
              // If not JSON, treat as raw text chunk
              store.appendAssistantChunk(msg.data)
            }
          },

          onerror: (err) => {
            if (ctrl.signal.aborted) return
            store.setError(
              err instanceof Error ? err.message : 'Connection lost'
            )
            throw err
          },

          openWhenHidden: true,
        })

        // Stream completed
        store.finalizeAssistant()
      } catch (err) {
        if (!ctrl.signal.aborted) {
          store.setError(
            err instanceof Error ? err.message : 'Failed to send message'
          )
        }
      }
    },
    [store]
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    store.finalizeAssistant()
  }, [store])

  return {
    sendMessage,
    cancel,
    messages: store.messages,
    isStreaming: store.isStreaming,
    error: store.error,
    sessionId: store.sessionId,
    reset: store.reset,
  }
}
