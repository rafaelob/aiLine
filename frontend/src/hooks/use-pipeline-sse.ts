'use client'

import { useCallback, useRef, useEffect } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { usePipelineStore } from '@/stores/pipeline-store'
import type { PipelineEvent } from '@/types/pipeline'
import type { PlanGenerationRequest, StudyPlan, QualityReport } from '@/types/plan'
import type { ScorecardData } from '@/components/plan/transformation-scorecard'
import { API_BASE, getAuthHeaders } from '@/lib/api'

/**
 * SSE hook for the plan generation pipeline.
 * Connects to /plans/generate/stream and feeds typed events into Zustand.
 */

export function usePipelineSSE() {
  const abortRef = useRef<AbortController | null>(null)
  const store = usePipelineStore()

  // Abort SSE connection on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

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
            ...getAuthHeaders(),
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
                store.setPlan(event.payload.plan as StudyPlan)
              }

              // Extract scorecard from run.completed payload
              if (event.type === 'run.completed' && event.payload?.scorecard) {
                store.setScorecard(event.payload.scorecard as ScorecardData)
              }

              // Extract quality report
              if (event.type === 'quality.scored' && event.payload) {
                store.setQualityReport(event.payload as unknown as QualityReport)
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
    scorecard: store.scorecard,
    isRunning: store.isRunning,
    error: store.error,
  }
}
