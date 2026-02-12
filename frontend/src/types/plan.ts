/**
 * Study plan types matching domain entities from the backend.
 */

export interface StudyPlan {
  id: string
  title: string
  subject: string
  grade: string
  objectives: string[]
  activities: Activity[]
  assessments: Assessment[]
  accessibility_notes: string[]
  curriculum_alignment: CurriculumAlignment[]
  created_at: string
  updated_at: string
}

export interface Activity {
  title: string
  description: string
  duration_minutes: number
  materials: string[]
  adaptations: Adaptation[]
}

export interface Adaptation {
  profile: string
  description: string
}

export interface Assessment {
  title: string
  type: string
  criteria: string[]
  adaptations: Adaptation[]
}

export interface CurriculumAlignment {
  standard_id: string
  standard_name: string
  description: string
}

export interface QualityReport {
  score: number
  structural_checks: StructuralCheck[]
  suggestions: string[]
  decision: 'accept' | 'refine' | 'must-refine'
}

export interface StructuralCheck {
  name: string
  passed: boolean
  message: string
}

export interface PlanExport {
  variant: string
  format: string
  content: string
}

export interface PlanGenerationRequest {
  prompt: string
  grade: string
  subject: string
  accessibility_profile: string
  locale: string
}
