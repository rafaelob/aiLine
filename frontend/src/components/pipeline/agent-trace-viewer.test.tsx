import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AgentTraceViewer } from './agent-trace-viewer'
import type { AgentTrace } from '@/types/trace'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockTrace: AgentTrace = {
  run_id: 'run-001',
  nodes: [
    {
      node_name: 'Planner',
      status: 'completed',
      time_ms: 120,
      tool_calls: ['search_curriculum', 'get_bncc'],
      quality_score: null,
      started_at: '2026-02-13T10:00:00Z',
      completed_at: '2026-02-13T10:00:00.120Z',
    },
    {
      node_name: 'QualityGate',
      status: 'completed',
      time_ms: 45,
      tool_calls: [],
      quality_score: 85,
      started_at: '2026-02-13T10:00:00.120Z',
      completed_at: '2026-02-13T10:00:00.165Z',
    },
    {
      node_name: 'Executor',
      status: 'running',
      time_ms: 200,
      tool_calls: ['generate_plan'],
      quality_score: null,
      started_at: '2026-02-13T10:00:00.165Z',
      completed_at: null,
    },
  ],
  total_time_ms: 365,
  model_used: 'claude-haiku-4-5',
}

describe('AgentTraceViewer', () => {
  const user = userEvent.setup()

  it('renders no trace message when trace is null', () => {
    render(<AgentTraceViewer trace={null} />)
    expect(screen.getByText('trace.no_trace')).toBeInTheDocument()
  })

  it('renders all trace nodes', () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    expect(screen.getByText('Planner')).toBeInTheDocument()
    expect(screen.getByText('QualityGate')).toBeInTheDocument()
    expect(screen.getByText('Executor')).toBeInTheDocument()
  })

  it('shows time_ms for each node', () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    expect(screen.getByText('120ms')).toBeInTheDocument()
    expect(screen.getByText('45ms')).toBeInTheDocument()
    expect(screen.getByText('200ms')).toBeInTheDocument()
  })

  it('shows quality score badge when present', () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('shows total time footer', () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    expect(screen.getByText('365ms')).toBeInTheDocument()
  })

  it('expands node details on click', async () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    const plannerButton = screen.getByText('Planner').closest('button')!
    await user.click(plannerButton)

    expect(screen.getByText('search_curriculum')).toBeInTheDocument()
    expect(screen.getByText('get_bncc')).toBeInTheDocument()
  })

  it('collapses node details on second click', async () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    const plannerButton = screen.getByText('Planner').closest('button')!
    await user.click(plannerButton)
    expect(screen.getByText('search_curriculum')).toBeInTheDocument()

    await user.click(plannerButton)
    expect(screen.queryByText('search_curriculum')).not.toBeInTheDocument()
  })

  it('has proper list role', () => {
    render(<AgentTraceViewer trace={mockTrace} />)
    const list = screen.getByRole('list')
    expect(list).toBeInTheDocument()
  })
})
