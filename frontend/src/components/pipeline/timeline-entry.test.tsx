import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TimelineEntry } from './timeline-entry'
import type { PipelineEvent } from '@/types/pipeline'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

function makeEvent(overrides: Partial<PipelineEvent>): PipelineEvent {
  return {
    run_id: 'test-run',
    seq: 1,
    ts: '2026-01-01T00:00:01Z',
    type: 'stage.started',
    stage: 'planning',
    payload: {},
    ...overrides,
  }
}

describe('TimelineEntry', () => {
  const runStartTs = '2026-01-01T00:00:00Z'

  it('renders as a listitem', () => {
    render(
      <TimelineEntry
        event={makeEvent({})}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByRole('listitem')).toBeInTheDocument()
  })

  it('shows the event type label from translations', () => {
    render(
      <TimelineEntry
        event={makeEvent({ type: 'stage.started' })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByText('pipeline.event_types.stage.started')).toBeInTheDocument()
  })

  it('shows relative timestamp', () => {
    render(
      <TimelineEntry
        event={makeEvent({ ts: '2026-01-01T00:00:01.500Z' })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    // +1.5s appears in both the timestamp column and the latency badge
    const matches = screen.getAllByText('+1.5s')
    expect(matches.length).toBe(2)
  })

  it('shows model rationale when model is in payload', () => {
    render(
      <TimelineEntry
        event={makeEvent({
          type: 'stage.started',
          payload: { model: 'gemini-2.0-flash', confidence: 0.82 },
        })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByText('gemini-2.0-flash, 82%')).toBeInTheDocument()
  })

  it('shows score rationale when score is in payload', () => {
    render(
      <TimelineEntry
        event={makeEvent({
          type: 'quality.scored',
          payload: { score: 87 },
        })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByText('87/100')).toBeInTheDocument()
  })

  it('shows decision rationale for quality decision events', () => {
    render(
      <TimelineEntry
        event={makeEvent({
          type: 'quality.decision',
          payload: { decision: 'accept' },
        })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByText('accept')).toBeInTheDocument()
  })

  it('returns null for heartbeat events', () => {
    const { container } = render(
      <TimelineEntry
        event={makeEvent({ type: 'heartbeat' })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(container.innerHTML).toBe('')
  })

  it('shows latency badge with aria-label', () => {
    render(
      <TimelineEntry
        event={makeEvent({ ts: '2026-01-01T00:00:02Z' })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    const badge = screen.getByLabelText('pipeline.latency: +2.0s')
    expect(badge).toBeInTheDocument()
  })

  it('shows tool name from payload', () => {
    render(
      <TimelineEntry
        event={makeEvent({
          type: 'tool.started',
          payload: { tool_name: 'search_bncc' },
        })}
        index={0}
        runStartTs={runStartTs}
      />
    )
    expect(screen.getByText('search_bncc')).toBeInTheDocument()
  })
})
