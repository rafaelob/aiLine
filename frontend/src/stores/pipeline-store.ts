import { create } from 'zustand'
import type {
  PipelineEvent,
  PipelineStage,
  StageInfo,
  StageStatus,
} from '@/types/pipeline'
import type { StudyPlan, QualityReport } from '@/types/plan'
import type { ScorecardData } from '@/components/plan/transformation-scorecard'

/**
 * Pipeline state store (Zustand 5.x).
 * Drives the Glass Box pipeline viewer with real-time SSE updates.
 */

const STAGE_ORDER: PipelineStage[] = [
  'planning',
  'validation',
  'refinement',
  'execution',
  'done',
]

function createInitialStages(): StageInfo[] {
  return STAGE_ORDER.map((id) => ({
    id,
    label: id,
    description: '',
    status: 'pending' as StageStatus,
    progress: 0,
    startedAt: null,
    completedAt: null,
  }))
}

export interface PipelineState {
  runId: string | null
  currentStage: PipelineStage | null
  stages: StageInfo[]
  events: PipelineEvent[]
  plan: StudyPlan | null
  qualityReport: QualityReport | null
  score: number | null
  scorecard: ScorecardData | null
  isRunning: boolean
  error: string | null

  // Actions
  startRun: (runId: string) => void
  addEvent: (event: PipelineEvent) => void
  setPlan: (plan: StudyPlan) => void
  setQualityReport: (report: QualityReport) => void
  setScore: (score: number) => void
  setScorecard: (scorecard: ScorecardData) => void
  setError: (error: string) => void
  reset: () => void
}

function updateStageStatus(
  stages: StageInfo[],
  stageId: PipelineStage,
  status: StageStatus,
  ts: string
): StageInfo[] {
  return stages.map((s) => {
    if (s.id !== stageId) return s
    return {
      ...s,
      status,
      startedAt: status === 'active' ? ts : s.startedAt,
      completedAt: status === 'completed' || status === 'failed' ? ts : s.completedAt,
      progress: status === 'completed' ? 100 : status === 'failed' ? s.progress : s.progress,
    }
  })
}

function updateStageProgress(
  stages: StageInfo[],
  stageId: PipelineStage,
  progress: number
): StageInfo[] {
  return stages.map((s) => {
    if (s.id !== stageId) return s
    return { ...s, progress: Math.min(100, Math.max(0, progress)) }
  })
}

export const usePipelineStore = create<PipelineState>((set) => ({
  runId: null,
  currentStage: null,
  stages: createInitialStages(),
  events: [],
  plan: null,
  qualityReport: null,
  score: null,
  scorecard: null,
  isRunning: false,
  error: null,

  startRun: (runId: string) =>
    set({
      runId,
      currentStage: null,
      stages: createInitialStages(),
      events: [],
      plan: null,
      qualityReport: null,
      score: null,
      scorecard: null,
      isRunning: true,
      error: null,
    }),

  addEvent: (event: PipelineEvent) =>
    set((state) => {
      let stages = [...state.stages]
      let currentStage = state.currentStage
      let score = state.score

      switch (event.type) {
        case 'stage.started':
          if (event.stage) {
            stages = updateStageStatus(stages, event.stage, 'active', event.ts)
            currentStage = event.stage
          }
          break

        case 'stage.progress':
          if (event.stage) {
            const progress =
              typeof event.payload?.progress === 'number'
                ? event.payload.progress
                : 0
            stages = updateStageProgress(stages, event.stage, progress)
          }
          break

        case 'stage.completed':
          if (event.stage) {
            stages = updateStageStatus(stages, event.stage, 'completed', event.ts)
          }
          break

        case 'stage.failed':
          if (event.stage) {
            stages = updateStageStatus(stages, event.stage, 'failed', event.ts)
          }
          break

        case 'quality.scored':
          if (typeof event.payload?.score === 'number') {
            score = event.payload.score
          }
          break

        case 'run.completed':
          currentStage = 'done'
          stages = updateStageStatus(stages, 'done', 'completed', event.ts)
          break

        case 'run.failed':
          break
      }

      const MAX_EVENTS = 100
      const cappedEvents = state.events.length >= MAX_EVENTS
        ? [...state.events.slice(1), event]
        : [...state.events, event]

      return {
        events: cappedEvents,
        stages,
        currentStage,
        score,
        isRunning: event.type !== 'run.completed' && event.type !== 'run.failed',
      }
    }),

  setPlan: (plan: StudyPlan) => set({ plan }),

  setQualityReport: (report: QualityReport) =>
    set({ qualityReport: report, score: report.score }),

  setScore: (score: number) => set({ score }),

  setScorecard: (scorecard: ScorecardData) => set({ scorecard }),

  setError: (error: string) => set({ error, isRunning: false }),

  reset: () =>
    set({
      runId: null,
      currentStage: null,
      stages: createInitialStages(),
      events: [],
      plan: null,
      qualityReport: null,
      score: null,
      scorecard: null,
      isRunning: false,
      error: null,
    }),
}))
