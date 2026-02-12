import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineViewer } from './pipeline-viewer'
import type { StageInfo } from '@/types/pipeline'

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
    svg: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <svg {...safe}>{children as React.ReactNode}</svg>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('./stage-card', () => ({
  StageCard: ({ stage }: { stage: StageInfo }) => (
    <div role="listitem" data-testid={`stage-${stage.id}`}>
      {stage.id}
    </div>
  ),
}))

const mockStages: StageInfo[] = [
  {
    id: 'planning',
    label: 'Planning',
    description: 'Planning step',
    status: 'completed',
    progress: 100,
    startedAt: '2026-01-01T00:00:00Z',
    completedAt: '2026-01-01T00:01:00Z',
  },
  {
    id: 'validation',
    label: 'Validation',
    description: 'Validating',
    status: 'active',
    progress: 50,
    startedAt: '2026-01-01T00:01:00Z',
    completedAt: null,
  },
  {
    id: 'execution',
    label: 'Execution',
    description: 'Executing',
    status: 'pending',
    progress: 0,
    startedAt: null,
    completedAt: null,
  },
]

describe('PipelineViewer', () => {
  it('renders as a section with accessible label', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    // The section uses aria-label={t('title')} which translates to 'pipeline.title'
    const section = screen.getByRole('region', { name: 'pipeline.title' })
    expect(section).toBeInTheDocument()
  })

  it('renders the title', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    expect(screen.getByText('pipeline.title')).toBeInTheDocument()
  })

  it('renders the glass box label', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    expect(screen.getByText('pipeline.glass_box')).toBeInTheDocument()
  })

  it('renders all stage cards', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    expect(screen.getByTestId('stage-planning')).toBeInTheDocument()
    expect(screen.getByTestId('stage-validation')).toBeInTheDocument()
    expect(screen.getByTestId('stage-execution')).toBeInTheDocument()
  })

  it('shows error alert when error is present', () => {
    render(
      <PipelineViewer
        stages={mockStages}
        isRunning={false}
        error="Something went wrong"
      />
    )
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Something went wrong')
  })

  it('does not show error when error is null', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders stage list container', () => {
    render(
      <PipelineViewer stages={mockStages} isRunning={true} error={null} />
    )
    const list = screen.getByRole('list', { name: 'pipeline.title' })
    expect(list).toBeInTheDocument()
  })
})
