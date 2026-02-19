import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThoughtPanel } from './thought-panel'
import type { PipelineEvent, StageInfo } from '@/types/pipeline'

function makeStages(overrides: Partial<StageInfo>[] = []): StageInfo[] {
  const defaults: StageInfo[] = [
    { id: 'planning', label: 'planning', description: '', status: 'completed', progress: 100, startedAt: '2026-01-01T00:00:00Z', completedAt: '2026-01-01T00:00:01Z' },
    { id: 'validation', label: 'validation', description: '', status: 'active', progress: 50, startedAt: '2026-01-01T00:00:01Z', completedAt: null },
    { id: 'refinement', label: 'refinement', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'execution', label: 'execution', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'done', label: 'done', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
  ]
  return defaults.map((s, i) => ({ ...s, ...(overrides[i] ?? {}) }))
}

function makeEvents(types: Array<{ type: string; stage?: string; payload?: Record<string, unknown> }>): PipelineEvent[] {
  return types.map((t, i) => ({
    run_id: 'r1',
    seq: i + 1,
    ts: `2026-01-01T00:00:0${i}Z`,
    type: t.type as PipelineEvent['type'],
    stage: (t.stage as PipelineEvent['stage']) ?? null,
    payload: t.payload ?? {},
  }))
}

describe('ThoughtPanel', () => {
  it('renders nothing when no events and not running', () => {
    const { container } = render(
      <ThoughtPanel stages={[]} events={[]} isRunning={false} />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders with role="complementary" and aria-label', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    const aside = screen.getByRole('complementary')
    expect(aside).toBeInTheDocument()
    expect(aside).toHaveAttribute('aria-label', 'thoughtPanel.panel_label')
  })

  it('has an expandable/collapsible toggle button', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    const toggle = screen.getByRole('button', { name: /thoughtPanel\.title/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('displays steps from SSE events', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
      { type: 'stage.completed', stage: 'planning' },
      { type: 'quality.scored', payload: { score: 85 } },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    // quality score step
    expect(screen.getByText('pipeline.event_types.quality.scored')).toBeInTheDocument()
    // quality score display
    expect(screen.getByText('85/100')).toBeInTheDocument()
  })

  it('displays activated skills from tool events', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
      { type: 'tool.started', payload: { tool_name: 'lesson-planner' } },
      { type: 'tool.completed', payload: { tool_name: 'lesson-planner' } },
      { type: 'tool.started', payload: { tool_name: 'quiz-generator' } },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    // Each tool name appears twice: once in the step log and once in the skills section
    expect(screen.getAllByText('lesson-planner').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('quiz-generator').length).toBeGreaterThanOrEqual(1)
  })

  it('displays RAG citations from events', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
      { type: 'run.completed', payload: { citations: ['Source A', 'Source B'] } },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={false} />,
    )
    expect(screen.getByText('Source A')).toBeInTheDocument()
    expect(screen.getByText('Source B')).toBeInTheDocument()
  })

  it('shows step count in header', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
      { type: 'stage.completed', stage: 'planning' },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    // stage.completed updates the existing step, so count stays 1
    expect(screen.getByText('(1)')).toBeInTheDocument()
  })

  it('has aria-live log region', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={true} />,
    )
    const log = screen.getByRole('log')
    expect(log).toHaveAttribute('aria-live', 'polite')
  })

  it('displays run.failed with error detail', () => {
    const events = makeEvents([
      { type: 'stage.started', stage: 'planning' },
      { type: 'run.failed', payload: { error: 'Timeout exceeded' } },
    ])
    render(
      <ThoughtPanel stages={makeStages()} events={events} isRunning={false} />,
    )
    expect(screen.getByText('pipeline.event_types.run.failed')).toBeInTheDocument()
    expect(screen.getByText('Timeout exceeded')).toBeInTheDocument()
  })
})
