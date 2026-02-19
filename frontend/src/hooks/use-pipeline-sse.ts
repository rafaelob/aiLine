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
  const retryCountRef = useRef(0)
  const generationIdRef = useRef(0)

  // Granular selectors to avoid re-rendering on every SSE event
  const runId = usePipelineStore((s) => s.runId)
  const stages = usePipelineStore((s) => s.stages)
  const events = usePipelineStore((s) => s.events)
  const currentStage = usePipelineStore((s) => s.currentStage)
  const plan = usePipelineStore((s) => s.plan)
  const qualityReport = usePipelineStore((s) => s.qualityReport)
  const score = usePipelineStore((s) => s.score)
  const scorecard = usePipelineStore((s) => s.scorecard)
  const isRunning = usePipelineStore((s) => s.isRunning)
  const error = usePipelineStore((s) => s.error)

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
      retryCountRef.current = 0
      const currentGenId = ++generationIdRef.current

      usePipelineStore.getState().reset()

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
              // Don't retry on client errors
              if (response.status >= 400 && response.status < 500) {
                ctrl.abort()
                usePipelineStore.getState().setError(
                  `SSE connection failed: ${response.status} ${response.statusText}`
                )
                return
              }
              throw new Error(
                `SSE connection failed: ${response.status} ${response.statusText}`
              )
            }
            // Reset retry count on successful connection
            retryCountRef.current = 0
          },

          onmessage: (msg) => {
            if (!msg.data) return

            try {
              const event: PipelineEvent = JSON.parse(msg.data)
              const s = usePipelineStore.getState()

              // Initialize run on first event
              if (event.type === 'run.started' && event.run_id) {
                s.startRun(event.run_id)
              }

              s.addEvent(event)

              // Extract plan from run.completed payload
              if (event.type === 'run.completed' && event.payload?.plan) {
                s.setPlan(event.payload.plan as StudyPlan)
              }

              // Extract scorecard from run.completed payload
              if (event.type === 'run.completed' && event.payload?.scorecard) {
                s.setScorecard(event.payload.scorecard as ScorecardData)
              }

              // Extract quality report
              if (event.type === 'quality.scored' && event.payload) {
                s.setQualityReport(event.payload as unknown as QualityReport)
              }
            } catch {
              // Skip malformed events silently
            }
          },

          onerror: (err) => {
            if (ctrl.signal.aborted) return
            // Stale generation guard — don't set error for old generations
            if (currentGenId !== generationIdRef.current) return

            retryCountRef.current++
            if (retryCountRef.current > 3) {
              usePipelineStore.getState().setError(
                err instanceof Error ? err.message : 'Connection lost'
              )
              ctrl.abort()
              return // Stop retrying (don't throw)
            }
            // Allow retry by not throwing
          },

          openWhenHidden: true, // Keep SSE alive when tab is hidden
        })
      } catch (err) {
        if (!ctrl.signal.aborted) {
          usePipelineStore.getState().setError(
            err instanceof Error ? err.message : 'Failed to start generation'
          )
        }
      }
    },
    []
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    usePipelineStore.getState().setError('Generation cancelled')
  }, [])

  return {
    startGeneration,
    cancel,
    runId,
    stages,
    events,
    currentStage,
    plan,
    qualityReport,
    score,
    scorecard,
    isRunning,
    error,
  }
}
