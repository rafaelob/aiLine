import { describe, it, expect } from 'vitest'
import type {
  PersonaId,
  Persona,
  ExportVariant,
  SimulationMode,
  DiffChange,
  TwinTab,
} from './accessibility'
import type {
  PipelineEventType,
  PipelineEvent,
  PipelineStage,
  StageStatus,
  StageInfo,
} from './pipeline'
import type {
  StudyPlan,
  Activity,
  Adaptation,
  Assessment,
  QualityReport,
  PlanGenerationRequest,
} from './plan'
import type {
  RecognitionResult,
  GestureInfo,
  GestureListResponse,
  CaptureState,
  WebcamErrorCode,
} from './sign-language'
import type {
  RenderedExport,
  StepType,
  ScheduleStep,
} from './exports'

describe('Type exports verification', () => {
  it('accessibility types are importable', () => {
    const persona: PersonaId = 'standard'
    const variant: ExportVariant = 'standard'
    const mode: SimulationMode = 'protanopia'
    const tab: TwinTab = 'original'
    const change: DiffChange = { type: 'unchanged', text: 'test' }
    const p: Persona = {
      id: 'standard',
      label: 'Standard',
      icon: 'U',
      theme: 'standard',
      description: 'Default',
    }
    expect(persona).toBe('standard')
    expect(variant).toBe('standard')
    expect(mode).toBe('protanopia')
    expect(tab).toBe('original')
    expect(change.type).toBe('unchanged')
    expect(p.id).toBe('standard')
  })

  it('pipeline types are importable', () => {
    const eventType: PipelineEventType = 'run.started'
    const stage: PipelineStage = 'planning'
    const status: StageStatus = 'pending'
    const event: PipelineEvent = {
      run_id: '123',
      seq: 1,
      ts: '2026-01-01',
      type: 'run.started',
      stage: null,
      payload: {},
    }
    const stageInfo: StageInfo = {
      id: 'planning',
      label: 'Planning',
      description: 'Test',
      status: 'pending',
      progress: 0,
      startedAt: null,
      completedAt: null,
    }
    expect(eventType).toBe('run.started')
    expect(stage).toBe('planning')
    expect(status).toBe('pending')
    expect(event.run_id).toBe('123')
    expect(stageInfo.id).toBe('planning')
  })

  it('plan types are importable', () => {
    const adaptation: Adaptation = { profile: 'TEA', description: 'Visual aids' }
    const activity: Activity = {
      title: 'Test',
      description: 'Desc',
      duration_minutes: 10,
      materials: [],
      adaptations: [adaptation],
    }
    const assessment: Assessment = {
      title: 'Quiz',
      type: 'formative',
      criteria: ['criterion'],
      adaptations: [],
    }
    const plan: StudyPlan = {
      id: '1',
      title: 'Plan',
      subject: 'Math',
      grade: '5th',
      objectives: ['Learn'],
      activities: [activity],
      assessments: [assessment],
      accessibility_notes: [],
      curriculum_alignment: [],
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
    }
    const report: QualityReport = {
      score: 85,
      structural_checks: [],
      suggestions: [],
      decision: 'accept',
    }
    const request: PlanGenerationRequest = {
      prompt: 'Test',
      grade: '5th',
      subject: 'Math',
      accessibility_profile: 'standard',
      locale: 'pt-BR',
    }
    expect(plan.id).toBe('1')
    expect(report.score).toBe(85)
    expect(request.prompt).toBe('Test')
  })

  it('sign-language types are importable', () => {
    const result: RecognitionResult = {
      gesture: 'oi',
      confidence: 0.95,
      landmarks: [],
      model: 'mlp-v1',
    }
    const gesture: GestureInfo = {
      id: 'oi',
      name_pt: 'Ola',
      name_en: 'Hello',
      name_es: 'Hola',
    }
    const response: GestureListResponse = {
      gestures: [gesture],
      model: 'mlp-v1',
      note: 'Test',
    }
    const state: CaptureState = 'idle'
    const error: WebcamErrorCode = 'not_allowed'
    expect(result.gesture).toBe('oi')
    expect(gesture.id).toBe('oi')
    expect(response.model).toBe('mlp-v1')
    expect(state).toBe('idle')
    expect(error).toBe('not_allowed')
  })

  it('exports types are importable', () => {
    const stepType: StepType = 'intro'
    const step: ScheduleStep = {
      stepNumber: 1,
      title: 'Test',
      description: 'Desc',
      durationMinutes: 10,
      type: 'intro',
    }
    const rendered: RenderedExport = {
      variant: 'standard',
      format: 'html',
      content: '<p>Test</p>',
    }
    expect(stepType).toBe('intro')
    expect(step.stepNumber).toBe(1)
    expect(rendered.variant).toBe('standard')
  })
})
