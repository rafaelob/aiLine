import { describe, it, expect, beforeEach } from 'vitest'
import { usePipelineStore } from './pipeline-store'
import type { PipelineEvent } from '@/types/pipeline'

function makeEvent(overrides: Partial<PipelineEvent>): PipelineEvent {
  return {
    run_id: 'test-run',
    seq: 0,
    ts: new Date().toISOString(),
    type: 'run.started',
    stage: null,
    payload: {},
    ...overrides,
  }
}

describe('pipeline-store', () => {
  beforeEach(() => {
    usePipelineStore.getState().reset()
  })

  it('has correct initial state', () => {
    const state = usePipelineStore.getState()
    expect(state.runId).toBeNull()
    expect(state.currentStage).toBeNull()
    expect(state.stages).toHaveLength(5)
    expect(state.events).toHaveLength(0)
    expect(state.plan).toBeNull()
    expect(state.qualityReport).toBeNull()
    expect(state.score).toBeNull()
    expect(state.isRunning).toBe(false)
    expect(state.error).toBeNull()
  })

  it('initializes all 5 stages as pending', () => {
    const stages = usePipelineStore.getState().stages
    const ids = stages.map((s) => s.id)
    expect(ids).toEqual(['planning', 'validation', 'refinement', 'execution', 'done'])
    for (const stage of stages) {
      expect(stage.status).toBe('pending')
      expect(stage.progress).toBe(0)
    }
  })

  it('sets runId and isRunning on startRun', () => {
    usePipelineStore.getState().startRun('run-42')

    const state = usePipelineStore.getState()
    expect(state.runId).toBe('run-42')
    expect(state.isRunning).toBe(true)
    expect(state.error).toBeNull()
  })

  it('resets state when startRun is called with new runId', () => {
    const store = usePipelineStore.getState()
    store.startRun('run-1')
    store.addEvent(makeEvent({ type: 'stage.started', stage: 'planning' }))
    store.startRun('run-2')

    const state = usePipelineStore.getState()
    expect(state.runId).toBe('run-2')
    expect(state.events).toHaveLength(0)
    expect(state.currentStage).toBeNull()
  })

  it('handles stage.started events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'planning' })
    )

    const state = usePipelineStore.getState()
    expect(state.currentStage).toBe('planning')
    const planningStage = state.stages.find((s) => s.id === 'planning')
    expect(planningStage?.status).toBe('active')
  })

  it('handles stage.progress events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'validation' })
    )
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.progress', stage: 'validation', payload: { progress: 65 } })
    )

    const validationStage = usePipelineStore.getState().stages.find(
      (s) => s.id === 'validation'
    )
    expect(validationStage?.progress).toBe(65)
  })

  it('clamps stage progress between 0 and 100', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.progress', stage: 'planning', payload: { progress: 150 } })
    )

    const planningStage = usePipelineStore.getState().stages.find(
      (s) => s.id === 'planning'
    )
    expect(planningStage?.progress).toBe(100)

    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.progress', stage: 'planning', payload: { progress: -10 } })
    )
    const updatedStage = usePipelineStore.getState().stages.find(
      (s) => s.id === 'planning'
    )
    expect(updatedStage?.progress).toBe(0)
  })

  it('handles stage.completed events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'planning' })
    )
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.completed', stage: 'planning' })
    )

    const planningStage = usePipelineStore.getState().stages.find(
      (s) => s.id === 'planning'
    )
    expect(planningStage?.status).toBe('completed')
    expect(planningStage?.progress).toBe(100)
  })

  it('handles stage.failed events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.failed', stage: 'execution' })
    )

    const executionStage = usePipelineStore.getState().stages.find(
      (s) => s.id === 'execution'
    )
    expect(executionStage?.status).toBe('failed')
  })

  it('handles quality.scored events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'quality.scored', stage: null, payload: { score: 85 } })
    )

    expect(usePipelineStore.getState().score).toBe(85)
  })

  it('handles run.completed events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'run.completed', stage: null })
    )

    const state = usePipelineStore.getState()
    expect(state.isRunning).toBe(false)
    expect(state.currentStage).toBe('done')
    const doneStage = state.stages.find((s) => s.id === 'done')
    expect(doneStage?.status).toBe('completed')
  })

  it('handles run.failed events', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'run.failed', stage: null })
    )

    expect(usePipelineStore.getState().isRunning).toBe(false)
  })

  it('accumulates events in order', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'planning', seq: 1 })
    )
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.completed', stage: 'planning', seq: 2 })
    )
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'validation', seq: 3 })
    )

    expect(usePipelineStore.getState().events).toHaveLength(3)
  })

  it('sets plan', () => {
    const plan = {
      id: 'plan-1',
      title: 'Test Plan',
      subject: 'Math',
      grade: '5th',
      objectives: ['Learn fractions'],
      activities: [],
      assessments: [],
      accessibility_notes: [],
      curriculum_alignment: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    usePipelineStore.getState().setPlan(plan)
    expect(usePipelineStore.getState().plan).toEqual(plan)
  })

  it('sets quality report and extracts score', () => {
    const report = {
      score: 92,
      structural_checks: [{ name: 'has_objectives', passed: true, message: 'OK' }],
      suggestions: ['Add more activities'],
      decision: 'accept' as const,
    }

    usePipelineStore.getState().setQualityReport(report)

    const state = usePipelineStore.getState()
    expect(state.qualityReport).toEqual(report)
    expect(state.score).toBe(92)
  })

  it('sets error and stops running', () => {
    usePipelineStore.getState().startRun('run-1')
    expect(usePipelineStore.getState().isRunning).toBe(true)

    usePipelineStore.getState().setError('Connection lost')

    const state = usePipelineStore.getState()
    expect(state.error).toBe('Connection lost')
    expect(state.isRunning).toBe(false)
  })

  it('resets to initial state', () => {
    usePipelineStore.getState().startRun('run-1')
    usePipelineStore.getState().addEvent(
      makeEvent({ type: 'stage.started', stage: 'planning' })
    )
    usePipelineStore.getState().setError('test')

    usePipelineStore.getState().reset()

    const state = usePipelineStore.getState()
    expect(state.runId).toBeNull()
    expect(state.events).toHaveLength(0)
    expect(state.isRunning).toBe(false)
    expect(state.error).toBeNull()
  })
})
