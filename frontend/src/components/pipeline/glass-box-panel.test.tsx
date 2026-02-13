import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GlassBoxPanel } from './glass-box-panel'
import type { PipelineEvent } from '@/types/pipeline'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('./pipeline-node-graph', () => ({
  PipelineNodeGraph: () => <div data-testid="node-graph">NodeGraph</div>,
}))

vi.mock('./timeline-entry', () => ({
  TimelineEntry: ({ event }: { event: PipelineEvent }) => (
    <div role="listitem" data-testid={`event-${event.seq}`}>
      {event.type}
    </div>
  ),
}))

const mockEvents: PipelineEvent[] = [
  {
    run_id: 'run-1',
    seq: 1,
    ts: '2026-01-01T00:00:00Z',
    type: 'run.started',
    stage: null,
    payload: {},
  },
  {
    run_id: 'run-1',
    seq: 2,
    ts: '2026-01-01T00:00:01Z',
    type: 'stage.started',
    stage: 'planning',
    payload: {},
  },
  {
    run_id: 'run-1',
    seq: 3,
    ts: '2026-01-01T00:00:02Z',
    type: 'stage.completed',
    stage: 'planning',
    payload: {},
  },
]

describe('GlassBoxPanel', () => {
  const defaultProps = {
    events: mockEvents,
    isRunning: true,
    score: null,
    error: null,
  }

  it('renders as a complementary aside with accessible label', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    const aside = screen.getByRole('complementary', { name: 'pipeline.glass_box' })
    expect(aside).toBeInTheDocument()
  })

  it('renders the glass box label and title', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    expect(screen.getByText('pipeline.glass_box')).toBeInTheDocument()
    expect(screen.getByText('pipeline.title')).toBeInTheDocument()
  })

  it('renders the node graph', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    expect(screen.getByTestId('node-graph')).toBeInTheDocument()
  })

  it('renders timeline events', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    expect(screen.getByTestId('event-1')).toBeInTheDocument()
    expect(screen.getByTestId('event-2')).toBeInTheDocument()
    expect(screen.getByTestId('event-3')).toBeInTheDocument()
  })

  it('renders timeline heading', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    expect(screen.getByText('pipeline.timeline')).toBeInTheDocument()
  })

  it('shows no_events message when there are no events', () => {
    render(<GlassBoxPanel {...defaultProps} events={[]} />)
    expect(screen.getByText('pipeline.no_events')).toBeInTheDocument()
  })

  it('shows error alert when error is present', () => {
    render(<GlassBoxPanel {...defaultProps} error="Network error" />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Network error')
  })

  it('does not show error alert when error is null', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('has a toggle button with aria-expanded', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    const toggle = screen.getByRole('button', { name: 'pipeline.toggle_panel' })
    expect(toggle).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('collapses and hides content when toggle is clicked', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    const toggle = screen.getByRole('button', { name: 'pipeline.toggle_panel' })

    fireEvent.click(toggle)

    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    // When collapsed, timeline and node graph should not be visible
    expect(screen.queryByTestId('node-graph')).not.toBeInTheDocument()
  })

  it('re-opens when toggled twice', () => {
    render(<GlassBoxPanel {...defaultProps} />)
    const toggle = screen.getByRole('button', { name: 'pipeline.toggle_panel' })

    fireEvent.click(toggle) // collapse
    fireEvent.click(toggle) // re-open

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByTestId('node-graph')).toBeInTheDocument()
  })

  it('filters out heartbeat events from the timeline', () => {
    const eventsWithHeartbeat: PipelineEvent[] = [
      ...mockEvents,
      {
        run_id: 'run-1',
        seq: 4,
        ts: '2026-01-01T00:00:03Z',
        type: 'heartbeat',
        stage: null,
        payload: { status: 'alive' },
      },
    ]
    render(<GlassBoxPanel {...defaultProps} events={eventsWithHeartbeat} />)
    // 3 visible events (heartbeat filtered out)
    expect(screen.queryByTestId('event-4')).not.toBeInTheDocument()
    expect(screen.getByTestId('event-1')).toBeInTheDocument()
    expect(screen.getByTestId('event-2')).toBeInTheDocument()
    expect(screen.getByTestId('event-3')).toBeInTheDocument()
  })
})
