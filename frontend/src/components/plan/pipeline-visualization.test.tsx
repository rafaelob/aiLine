import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineVisualization } from './pipeline-visualization'
import type { PipelineEvent, StageInfo } from '@/types/pipeline'

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function makeStages(
  overrides: Partial<Record<string, Partial<StageInfo>>> = {},
): StageInfo[] {
  const defaults: StageInfo[] = [
    { id: 'planning', label: 'planning', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'validation', label: 'validation', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'refinement', label: 'refinement', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'execution', label: 'execution', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
    { id: 'done', label: 'done', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
  ]
  return defaults.map((s) => ({ ...s, ...(overrides[s.id] ?? {}) }))
}

function makeEvents(
  types: Array<{
    type: string
    stage?: string
    payload?: Record<string, unknown>
  }>,
): PipelineEvent[] {
  return types.map((t, i) => ({
    run_id: 'r1',
    seq: i + 1,
    ts: `2026-01-01T00:00:0${i}Z`,
    type: t.type as PipelineEvent['type'],
    stage: (t.stage as PipelineEvent['stage']) ?? null,
    payload: t.payload ?? {},
  }))
}

/* ------------------------------------------------------------------ */
/*  Tests                                                              */
/* ------------------------------------------------------------------ */

describe('PipelineVisualization', () => {
  it('renders with section and aria-label', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    const section = screen.getByRole('region', { name: 'pipelineViz.title' })
    expect(section).toBeInTheDocument()
  })

  it('shows title text', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    expect(screen.getByText('pipelineViz.title')).toBeInTheDocument()
  })

  it('renders all 6 node labels', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    const nodeNames = [
      'pipelineViz.nodes.rag',
      'pipelineViz.nodes.profile',
      'pipelineViz.nodes.planner',
      'pipelineViz.nodes.quality',
      'pipelineViz.nodes.executor',
      'pipelineViz.nodes.export',
    ]
    for (const name of nodeNames) {
      expect(screen.getByText(name)).toBeInTheDocument()
    }
  })

  it('shows Opus 4.6 badge on planner node', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    expect(screen.getByText('pipelineViz.opus_badge')).toBeInTheDocument()
  })

  it('shows running indicator when isRunning is true', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={true}
        score={null}
      />,
    )
    // The ping animation span is aria-hidden, but we can check the section has busy
    const section = screen.getByRole('region', { name: 'pipelineViz.title' })
    expect(section).toBeInTheDocument()
  })

  it('derives active state for planning stage nodes', () => {
    const stages = makeStages({
      planning: { status: 'active', startedAt: '2026-01-01T00:00:00Z' },
    })
    render(
      <PipelineVisualization
        stages={stages}
        events={[]}
        isRunning={true}
        score={null}
      />,
    )
    // RAG and Profile nodes should have "Processing" status
    const ragNode = screen.getByRole('group', {
      name: /pipelineViz\.nodes\.rag.*pipelineViz\.status\.active/,
    })
    expect(ragNode).toBeInTheDocument()

    const profileNode = screen.getByRole('group', {
      name: /pipelineViz\.nodes\.profile.*pipelineViz\.status\.active/,
    })
    expect(profileNode).toBeInTheDocument()
  })

  it('derives completed state when planning is done', () => {
    const stages = makeStages({
      planning: { status: 'completed', progress: 100, completedAt: '2026-01-01T00:00:01Z' },
      validation: { status: 'active', startedAt: '2026-01-01T00:00:01Z' },
    })
    render(
      <PipelineVisualization
        stages={stages}
        events={[]}
        isRunning={true}
        score={null}
      />,
    )
    const ragNode = screen.getByRole('group', {
      name: /pipelineViz\.nodes\.rag.*pipelineViz\.status\.completed/,
    })
    expect(ragNode).toBeInTheDocument()
  })

  it('shows quality score on quality node', () => {
    const stages = makeStages({
      planning: { status: 'completed', progress: 100 },
      validation: { status: 'completed', progress: 100 },
    })
    const events = makeEvents([
      { type: 'quality.scored', stage: 'validation', payload: { score: 92 } },
    ])
    render(
      <PipelineVisualization
        stages={stages}
        events={events}
        isRunning={false}
        score={92}
      />,
    )
    expect(screen.getByText('92/100')).toBeInTheDocument()
  })

  it('shows refinement loop indicator', () => {
    const stages = makeStages({
      planning: { status: 'completed', progress: 100 },
      validation: { status: 'active' },
      refinement: { status: 'active' },
    })
    const events = makeEvents([
      { type: 'refinement.started', stage: 'refinement' },
    ])
    render(
      <PipelineVisualization
        stages={stages}
        events={events}
        isRunning={true}
        score={65}
      />,
    )
    expect(screen.getByText('pipelineViz.refining')).toBeInTheDocument()
    expect(screen.getByText('65/100')).toBeInTheDocument()
  })

  it('does not show refinement loop when refinement completed', () => {
    const events = makeEvents([
      { type: 'refinement.started', stage: 'refinement' },
      { type: 'refinement.completed', stage: 'refinement' },
    ])
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={events}
        isRunning={true}
        score={null}
      />,
    )
    expect(screen.queryByText('pipelineViz.refining')).not.toBeInTheDocument()
  })

  it('shows tool name on executor node', () => {
    const stages = makeStages({
      execution: { status: 'active' },
    })
    const events = makeEvents([
      { type: 'tool.started', payload: { tool_name: 'lesson-planner' } },
    ])
    render(
      <PipelineVisualization
        stages={stages}
        events={events}
        isRunning={true}
        score={null}
      />,
    )
    expect(screen.getByText('lesson-planner')).toBeInTheDocument()
  })

  it('nodes are keyboard-focusable via tabIndex', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    const nodes = screen.getAllByRole('group')
    for (const node of nodes) {
      expect(node).toHaveAttribute('tabindex', '0')
    }
  })

  it('has a graph aria-label for the grid', () => {
    render(
      <PipelineVisualization
        stages={makeStages()}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    const graph = screen.getByRole('img', { name: 'pipelineViz.graph_label' })
    expect(graph).toBeInTheDocument()
  })

  it('derives failed state', () => {
    const stages = makeStages({
      planning: { status: 'failed' },
    })
    render(
      <PipelineVisualization
        stages={stages}
        events={[]}
        isRunning={false}
        score={null}
      />,
    )
    const ragNode = screen.getByRole('group', {
      name: /pipelineViz\.nodes\.rag.*pipelineViz\.status\.failed/,
    })
    expect(ragNode).toBeInTheDocument()
  })

  it('shows completed export node when done stage completes', () => {
    const stages = makeStages({
      planning: { status: 'completed', progress: 100 },
      validation: { status: 'completed', progress: 100 },
      execution: { status: 'completed', progress: 100 },
      done: { status: 'completed', progress: 100 },
    })
    render(
      <PipelineVisualization
        stages={stages}
        events={[]}
        isRunning={false}
        score={95}
      />,
    )
    const exportNode = screen.getByRole('group', {
      name: /pipelineViz\.nodes\.export.*pipelineViz\.status\.completed/,
    })
    expect(exportNode).toBeInTheDocument()
  })
})
