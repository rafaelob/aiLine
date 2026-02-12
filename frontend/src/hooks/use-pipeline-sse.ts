'use client'

import { useCallback, useRef } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { usePipelineStore } from '@/stores/pipeline-store'
import type { PipelineEvent } from '@/types/pipeline'
import type { PlanGenerationRequest } from '@/types/plan'

/**
 * SSE hook for the plan generation pipeline.
 * Connects to /plans/generate/stream and feeds typed events into Zustand.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export function usePipelineSSE() {
  const abortRef = useRef<AbortController | null>(null)
  const store = usePipelineStore()

  const startGeneration = useCallback(
    async (request: PlanGenerationRequest) => {
      // Abort any previous run
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      store.reset()

      try {
        await fetchEventSource(`${API_BASE}/plans/generate/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(request),
          signal: ctrl.signal,

          onopen: async (response) => {
            if (!response.ok) {
              throw new Error(
                `SSE connection failed: ${response.status} ${response.statusText}`
              )
            }
          },

          onmessage: (msg) => {
            if (!msg.data) return

            try {
              const event: PipelineEvent = JSON.parse(msg.data)

              // Initialize run on first event
              if (event.type === 'run.started' && event.run_id) {
                store.startRun(event.run_id)
              }

              store.addEvent(event)

              // Extract plan from run.completed payload
              if (event.type === 'run.completed' && event.payload?.plan) {
                store.setPlan(event.payload.plan as never)
              }

              // Extract quality report
              if (event.type === 'quality.scored' && event.payload) {
                store.setQualityReport(event.payload as never)
              }
            } catch {
              // Skip malformed events silently
            }
          },

          onerror: (err) => {
            if (ctrl.signal.aborted) return
            store.setError(
              err instanceof Error ? err.message : 'Connection lost'
            )
            throw err // Retry handled by fetchEventSource
          },

          openWhenHidden: true, // Keep SSE alive when tab is hidden
        })
      } catch (err) {
        if (!ctrl.signal.aborted) {
          store.setError(
            err instanceof Error ? err.message : 'Failed to start generation'
          )
        }
      }
    },
    [store]
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    store.setError('Generation cancelled')
  }, [store])

  return {
    startGeneration,
    cancel,
    runId: store.runId,
    stages: store.stages,
    events: store.events,
    currentStage: store.currentStage,
    plan: store.plan,
    qualityReport: store.qualityReport,
    score: store.score,
    isRunning: store.isRunning,
    error: store.error,
  }
}
