/**
 * Export viewer types for plan export comparison.
 */

import type { ExportVariant } from './accessibility'

/** A single rendered plan export. */
export interface RenderedExport {
  variant: ExportVariant
  format: 'html' | 'markdown' | 'text'
  content: string
}

/** Visual schedule step for TEA/TDAH-friendly card view. */
export type StepType = 'intro' | 'develop' | 'close' | 'activity' | 'assessment'

export interface ScheduleStep {
  stepNumber: number
  title: string
  description: string
  durationMinutes: number
  type: StepType
  icon?: string
  materials?: string[]
  adaptations?: string[]
}

/** Visual schedule for the entire lesson plan. */
export interface VisualSchedule {
  planTitle: string
  totalDurationMinutes: number
  steps: ScheduleStep[]
}
