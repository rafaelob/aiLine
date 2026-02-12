import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PlansPage from './page'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('@/components/plan/plan-generation-flow', () => ({
  PlanGenerationFlow: () => (
    <div data-testid="plan-generation-flow">Plan Flow</div>
  ),
}))

vi.mock('@/hooks/use-pipeline-sse', () => ({
  usePipelineSSE: () => ({
    startGeneration: vi.fn(),
    cancel: vi.fn(),
    stages: [],
    plan: null,
    qualityReport: null,
    score: null,
    isRunning: false,
    error: null,
  }),
}))

describe('PlansPage', () => {
  it('renders the plans title from translations', () => {
    render(<PlansPage />)
    expect(screen.getByText('plans.title')).toBeInTheDocument()
  })

  it('renders the PlanGenerationFlow component', () => {
    render(<PlansPage />)
    expect(screen.getByTestId('plan-generation-flow')).toBeInTheDocument()
  })

  it('has a header element', () => {
    render(<PlansPage />)
    const header = screen.getByRole('banner')
    expect(header).toBeInTheDocument()
  })
})
