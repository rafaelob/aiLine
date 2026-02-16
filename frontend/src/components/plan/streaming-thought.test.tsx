import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StreamingThought } from './streaming-thought'
import type { StageInfo } from '@/types/pipeline'

vi.mock('motion/react', () => {
  function MockDiv({ children, ...rest }: Record<string, unknown>) {
    const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, style: _s, ...safe } = rest
    return <div {...safe}>{children as React.ReactNode}</div>
  }
  return {
    motion: { div: MockDiv },
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useReducedMotion: () => false,
  }
})

const STAGES: StageInfo[] = [
  { id: 'planning', label: 'planning', description: '', status: 'completed', progress: 100, startedAt: '2026-02-15T00:00:00Z', completedAt: '2026-02-15T00:00:01Z' },
  { id: 'validation', label: 'validation', description: '', status: 'active', progress: 50, startedAt: '2026-02-15T00:00:01Z', completedAt: null },
  { id: 'refinement', label: 'refinement', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
  { id: 'execution', label: 'execution', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
  { id: 'done', label: 'done', description: '', status: 'pending', progress: 0, startedAt: null, completedAt: null },
]

describe('StreamingThought', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when no stages and not running', () => {
    const { container } = render(<StreamingThought stages={[]} isRunning={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders stage labels when running', () => {
    render(<StreamingThought stages={STAGES} isRunning={true} />)
    expect(screen.getByText('pipeline.stages.planning')).toBeInTheDocument()
    expect(screen.getByText('pipeline.stages.validation')).toBeInTheDocument()
    expect(screen.getByText('pipeline.stages.refinement')).toBeInTheDocument()
  })

  it('shows thinking header when running', () => {
    render(<StreamingThought stages={STAGES} isRunning={true} />)
    expect(screen.getByText('streaming_thought.thinking')).toBeInTheDocument()
  })

  it('shows complete header when not running', () => {
    render(<StreamingThought stages={STAGES} isRunning={false} />)
    expect(screen.getByText('streaming_thought.complete')).toBeInTheDocument()
  })

  it('collapses content when toggle button is clicked', async () => {
    render(<StreamingThought stages={STAGES} isRunning={true} />)

    const toggleBtn = screen.getByRole('button', { expanded: true })
    await user.click(toggleBtn)

    expect(toggleBtn).toHaveAttribute('aria-expanded', 'false')
  })

  it('has a log role for accessibility', () => {
    render(<StreamingThought stages={STAGES} isRunning={true} />)
    expect(screen.getByRole('log')).toBeInTheDocument()
  })
})
