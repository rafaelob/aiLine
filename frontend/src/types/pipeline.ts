/**
 * Pipeline SSE event types matching the backend contract (ADR-024).
 * Envelope: {run_id, seq, ts, type, stage, payload}
 */

export type PipelineEventType =
  | 'run.started'
  | 'stage.started'
  | 'stage.progress'
  | 'stage.completed'
  | 'stage.failed'
  | 'quality.scored'
  | 'quality.decision'
  | 'refinement.started'
  | 'refinement.completed'
  | 'tool.started'
  | 'tool.completed'
  | 'ai_receipt'
  | 'run.completed'
  | 'run.failed'
  | 'heartbeat'

export interface PipelineEvent {
  run_id: string
  seq: number
  ts: string
  type: PipelineEventType
  stage: PipelineStage | null
  payload: Record<string, unknown>
}

export type PipelineStage =
  | 'planning'
  | 'validation'
  | 'refinement'
  | 'execution'
  | 'done'

export type StageStatus = 'pending' | 'active' | 'completed' | 'failed'

export interface StageInfo {
  id: PipelineStage
  label: string
  description: string
  status: StageStatus
  progress: number
  startedAt: string | null
  completedAt: string | null
}
