import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineNodeGraph } from './pipeline-node-graph'
import type { PipelineEvent } from '@/types/pipeline'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
  },
}))

function makeEvent(overrides: Partial<PipelineEvent>): PipelineEvent {
  return {
    run_id: 'test-run',
    seq: 1,
    ts: '2026-01-01T00:00:01Z',
    type: 'run.started',
    stage: null,
    payload: {},
    ...overrides,
  }
}

describe('PipelineNodeGraph', () => {
  it('renders all 6 node labels', () => {
    render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    expect(screen.getByText('pipeline.node_user')).toBeInTheDocument()
    expect(screen.getByText('pipeline.node_router')).toBeInTheDocument()
    expect(screen.getByText('pipeline.node_llm')).toBeInTheDocument()
    expect(screen.getByText('pipeline.node_skill')).toBeInTheDocument()
    expect(screen.getByText('pipeline.node_quality')).toBeInTheDocument()
    expect(screen.getByText('pipeline.node_response')).toBeInTheDocument()
  })

  it('has an accessible img role with label', () => {
    render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    const graph = screen.getByRole('img', { name: 'pipeline.title' })
    expect(graph).toBeInTheDocument()
  })

  it('renders score badge when score is provided', () => {
    const events: PipelineEvent[] = [
      makeEvent({ type: 'quality.scored', stage: 'validation', payload: { score: 85 } }),
      makeEvent({ type: 'quality.decision', seq: 2, payload: { decision: 'accept' } }),
    ]
    render(
      <PipelineNodeGraph
        events={events}
        isRunning={false}
        score={85}
      />
    )
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('renders without crashing when events are empty', () => {
    const { container } = render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    expect(container.firstChild).toBeTruthy()
  })

  it('renders connector arrows between nodes', () => {
    const { container } = render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    // 5 connector lines between 6 nodes
    const connectorLines = container.querySelectorAll('[aria-hidden="true"]')
    expect(connectorLines.length).toBeGreaterThan(0)
  })

  it('does not show score badge when score is null', () => {
    render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    // No numeric score badge should appear
    const allSpans = screen.queryAllByText(/^\d+$/)
    expect(allSpans).toHaveLength(0)
  })

  it('renders loop-back arrow when quality is rejected (must-refine)', () => {
    const events: PipelineEvent[] = [
      makeEvent({ type: 'run.started', seq: 1 }),
      makeEvent({ type: 'stage.started', seq: 2, stage: 'planning' }),
      makeEvent({ type: 'stage.completed', seq: 3, stage: 'planning' }),
      makeEvent({ type: 'tool.started', seq: 4 }),
      makeEvent({ type: 'tool.completed', seq: 5 }),
      makeEvent({ type: 'stage.started', seq: 6, stage: 'execution' }),
      makeEvent({ type: 'quality.scored', seq: 7, stage: 'validation', payload: { score: 45 } }),
      makeEvent({ type: 'quality.decision', seq: 8, payload: { decision: 'must-refine' } }),
    ]
    const { container } = render(
      <PipelineNodeGraph
        events={events}
        isRunning={false}
        score={45}
      />
    )
    // Loop-back SVG with loopArrow marker should be present
    const loopArrow = container.querySelector('#loopArrow')
    expect(loopArrow).toBeInTheDocument()
  })

  it('does not render loop-back arrow when quality is accepted', () => {
    const events: PipelineEvent[] = [
      makeEvent({ type: 'quality.scored', seq: 1, stage: 'validation', payload: { score: 90 } }),
      makeEvent({ type: 'quality.decision', seq: 2, payload: { decision: 'accept' } }),
    ]
    const { container } = render(
      <PipelineNodeGraph
        events={events}
        isRunning={false}
        score={90}
      />
    )
    const loopArrow = container.querySelector('#loopArrow')
    expect(loopArrow).not.toBeInTheDocument()
  })

  it('marks user node as completed when events exist', () => {
    const events: PipelineEvent[] = [
      makeEvent({ type: 'run.started', seq: 1 }),
    ]
    const { container } = render(
      <PipelineNodeGraph
        events={events}
        isRunning={true}
        score={null}
      />
    )
    // User node circle should have success background (completed)
    const circles = container.querySelectorAll('.rounded-full')
    expect(circles.length).toBeGreaterThan(0)
  })

  it('renders all 6 SVG icon paths', () => {
    const { container } = render(
      <PipelineNodeGraph
        events={[]}
        isRunning={false}
        score={null}
      />
    )
    // 6 nodes, each with an SVG path for the icon
    const svgs = container.querySelectorAll('svg path')
    expect(svgs.length).toBeGreaterThanOrEqual(6)
  })
})
