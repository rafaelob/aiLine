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
  const retryCountRef = useRef(0)

  // Granular selectors to avoid re-rendering on every streaming token
  const messages = useTutorStore((s) => s.messages)
  const isStreaming = useTutorStore((s) => s.isStreaming)
  const error = useTutorStore((s) => s.error)
  const sessionId = useTutorStore((s) => s.sessionId)
  const reset = useTutorStore((s) => s.reset)

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
      retryCountRef.current = 0

      const s = useTutorStore.getState()
      s.addUserMessage(message)
      s.startStreaming()

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
            session_id: useTutorStore.getState().sessionId,
          }),
          signal: ctrl.signal,

          onopen: async (response) => {
            if (!response.ok) {
              if (response.status >= 400 && response.status < 500) {
                ctrl.abort()
                useTutorStore.getState().setError(
                  `Tutor SSE failed: ${response.status} ${response.statusText}`
                )
                return
              }
              throw new Error(
                `Tutor SSE failed: ${response.status} ${response.statusText}`
              )
            }
            retryCountRef.current = 0
          },

          onmessage: (msg) => {
            if (!msg.data) return
            try {
              const data = JSON.parse(msg.data)
              const st = useTutorStore.getState()

              if (data.session_id && !st.sessionId) {
                st.setSessionId(data.session_id)
              }

              if (data.chunk) {
                st.appendAssistantChunk(data.chunk)
              }

              if (data.done) {
                st.finalizeAssistant()
              }
            } catch {
              // If not JSON, treat as raw text chunk
              useTutorStore.getState().appendAssistantChunk(msg.data)
            }
          },

          onerror: (err) => {
            if (ctrl.signal.aborted) return

            retryCountRef.current++
            if (retryCountRef.current > 3) {
              useTutorStore.getState().setError(
                err instanceof Error ? err.message : 'Connection lost'
              )
              ctrl.abort()
              return // Stop retrying
            }
          },

          openWhenHidden: true,
        })
      } catch (err) {
        if (!ctrl.signal.aborted) {
          useTutorStore.getState().setError(
            err instanceof Error ? err.message : 'Failed to send message'
          )
        }
      }
    },
    []
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    useTutorStore.getState().finalizeAssistant()
  }, [])

  return {
    sendMessage,
    cancel,
    messages,
    isStreaming,
    error,
    sessionId,
    reset,
  }
}
