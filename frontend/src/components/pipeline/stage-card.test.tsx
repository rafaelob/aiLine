import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StageCard } from './stage-card'
import type { StageInfo } from '@/types/pipeline'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    svg: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <svg {...safe}>{children as React.ReactNode}</svg>
    },
  },
}))

const baseStage: StageInfo = {
  id: 'planning',
  label: 'Planning',
  description: 'Generating plan',
  status: 'pending',
  progress: 0,
  startedAt: null,
  completedAt: null,
}

describe('StageCard', () => {
  it('renders as a listitem', () => {
    render(<StageCard stage={baseStage} index={0} isLast={false} />)
    const item = screen.getByRole('listitem')
    expect(item).toBeInTheDocument()
  })

  it('shows stage name from translations', () => {
    render(<StageCard stage={baseStage} index={0} isLast={false} />)
    expect(screen.getByText('pipeline.stages.planning')).toBeInTheDocument()
  })

  it('shows status badge from translations', () => {
    render(<StageCard stage={baseStage} index={0} isLast={false} />)
    expect(screen.getByText('pipeline.status.pending')).toBeInTheDocument()
  })

  it('shows step number for pending stages', () => {
    render(<StageCard stage={baseStage} index={0} isLast={false} />)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('shows progress bar for active stages with progress', () => {
    const activeStage: StageInfo = {
      ...baseStage,
      status: 'active',
      progress: 50,
    }
    render(<StageCard stage={activeStage} index={0} isLast={false} />)
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toBeInTheDocument()
    expect(progressBar).toHaveAttribute('aria-valuenow', '50')
  })

  it('does not show progress bar for pending stages', () => {
    render(<StageCard stage={baseStage} index={0} isLast={false} />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('renders connector line when not last', () => {
    const { container } = render(
      <StageCard stage={baseStage} index={0} isLast={false} />
    )
    const connectors = container.querySelectorAll('[aria-hidden="true"]')
    expect(connectors.length).toBeGreaterThan(0)
  })

  it('does not show progress bar for active stage with 0 progress', () => {
    const activeNoProgress: StageInfo = {
      ...baseStage,
      status: 'active',
      progress: 0,
    }
    render(<StageCard stage={activeNoProgress} index={0} isLast={false} />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })
})
