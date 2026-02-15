import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SmartRouterCard } from './smart-router-card'
import type { SmartRouterRationale } from '@/types/trace'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockRationale: SmartRouterRationale = {
  task_type: 'lesson_plan',
  model_selected: 'claude-haiku-4-5',
  weighted_scores: {
    tokens: 0.8,
    structured: 0.6,
    tools: 0.9,
    history: 0.4,
    intent: 0.7,
  },
  total_score: 0.72,
}

describe('SmartRouterCard', () => {
  const user = userEvent.setup()

  it('renders nothing when rationale is null', () => {
    const { container } = render(<SmartRouterCard rationale={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders model name badge', () => {
    render(<SmartRouterCard rationale={mockRationale} />)
    expect(screen.getByText('claude-haiku-4-5')).toBeInTheDocument()
  })

  it('expands to show score breakdown on click', async () => {
    render(<SmartRouterCard rationale={mockRationale} />)
    const badge = screen.getByLabelText('smart_router.why_model')
    await user.click(badge)

    expect(screen.getByText('smart_router.task_type')).toBeInTheDocument()
    expect(screen.getByText('lesson_plan')).toBeInTheDocument()
    expect(screen.getByText('smart_router.total')).toBeInTheDocument()
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  it('shows all 5 weight categories', async () => {
    render(<SmartRouterCard rationale={mockRationale} />)
    await user.click(screen.getByLabelText('smart_router.why_model'))

    expect(screen.getByText('smart_router.tokens')).toBeInTheDocument()
    expect(screen.getByText('smart_router.structured')).toBeInTheDocument()
    expect(screen.getByText('smart_router.tools')).toBeInTheDocument()
    expect(screen.getByText('smart_router.history')).toBeInTheDocument()
    expect(screen.getByText('smart_router.intent')).toBeInTheDocument()
  })

  it('collapses on second click', async () => {
    render(<SmartRouterCard rationale={mockRationale} />)
    const badge = screen.getByLabelText('smart_router.why_model')
    await user.click(badge)
    expect(screen.getByText('smart_router.task_type')).toBeInTheDocument()

    await user.click(badge)
    expect(screen.queryByText('smart_router.task_type')).not.toBeInTheDocument()
  })
})
