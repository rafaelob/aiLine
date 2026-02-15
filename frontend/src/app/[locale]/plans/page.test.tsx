import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PlansPage from './page'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, variants: _v, ...safe } = rest
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

vi.mock('@/components/plan/pending-reviews-badge', () => ({
  PendingReviewsBadge: () => (
    <div data-testid="pending-reviews-badge">Pending Reviews</div>
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

const defaultParams = Promise.resolve({ locale: 'pt-BR' })

describe('PlansPage', () => {
  it('renders the plans title from translations', async () => {
    const page = await PlansPage({ params: defaultParams })
    render(page)
    expect(screen.getByText('plans.title')).toBeInTheDocument()
  })

  it('renders the PlanGenerationFlow component', async () => {
    const page = await PlansPage({ params: defaultParams })
    render(page)
    expect(screen.getByTestId('plan-generation-flow')).toBeInTheDocument()
  })

  it('has a header element', async () => {
    const page = await PlansPage({ params: defaultParams })
    render(page)
    const header = screen.getByRole('banner')
    expect(header).toBeInTheDocument()
  })

  it('renders an h1 heading', async () => {
    const page = await PlansPage({ params: defaultParams })
    render(page)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading.textContent).toBe('plans.title')
  })

  it('wraps content in a max-width container', async () => {
    const page = await PlansPage({ params: defaultParams })
    const { container } = render(page)
    // PageTransition wraps the content
    const pageTransition = container.firstChild as HTMLElement
    const innerDiv = pageTransition.firstChild as HTMLElement
    expect(innerDiv.className).toContain('max-w-5xl')
    expect(innerDiv.className).toContain('mx-auto')
  })

  it('includes spacing between header and plan flow', async () => {
    const page = await PlansPage({ params: defaultParams })
    const { container } = render(page)
    // PageTransition wraps the content
    const pageTransition = container.firstChild as HTMLElement
    const innerDiv = pageTransition.firstChild as HTMLElement
    expect(innerDiv.className).toContain('space-y')
  })

  it('renders a single root element', async () => {
    const page = await PlansPage({ params: defaultParams })
    const { container } = render(page)
    expect(container.children).toHaveLength(1)
  })
})
