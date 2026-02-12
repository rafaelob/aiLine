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
        currentStage={null}
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
        currentStage={null}
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
        currentStage="validation"
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
        currentStage={null}
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
        currentStage={null}
        isRunning={false}
        score={null}
      />
    )
    // 5 connector lines between 6 nodes
    const connectorLines = container.querySelectorAll('[aria-hidden="true"]')
    expect(connectorLines.length).toBeGreaterThan(0)
  })
})
