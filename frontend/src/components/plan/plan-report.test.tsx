import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanReport } from './plan-report'
import type { QualityReport } from '@/types/plan'

vi.mock('motion/react', () => ({
  motion: {
    circle: (props: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = props
      return <circle {...safe} />
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, style, ...safe } = rest
      return <span style={style as React.CSSProperties} {...safe}>{children as React.ReactNode}</span>
    },
  },
  useSpring: (initial: number) => ({
    set: vi.fn(),
    get: () => initial,
    on: (_event: string, cb: (v: number) => void) => {
      cb(initial)
      return () => {}
    },
  }),
  useTransform: (_spring: unknown, transform: (v: number) => number) => ({
    get: () => transform(0),
    on: (_event: string, cb: (v: number) => void) => {
      cb(transform(0))
      return () => {}
    },
  }),
}))

const mockReport: QualityReport = {
  score: 85,
  structural_checks: [
    { name: 'Has objectives', passed: true, message: 'At least 2 objectives found' },
    { name: 'Has assessments', passed: false, message: 'No assessments found' },
  ],
  suggestions: ['Add more activities', 'Include adaptations'],
  decision: 'accept',
}

describe('PlanReport', () => {
  it('shows empty state when no report and no score', () => {
    render(<PlanReport report={null} score={null} />)
    expect(screen.getByText('quality.no_report')).toBeInTheDocument()
  })

  it('renders score gauge when score is provided', () => {
    render(<PlanReport report={null} score={75} />)
    const meter = screen.getByRole('meter')
    expect(meter).toBeInTheDocument()
  })

  it('renders decision badge when report has decision', () => {
    render(<PlanReport report={mockReport} score={85} />)
    expect(screen.getByText('quality.decision.accept')).toBeInTheDocument()
  })

  it('renders structural checks', () => {
    render(<PlanReport report={mockReport} score={85} />)
    expect(screen.getByText('Has objectives')).toBeInTheDocument()
    expect(screen.getByText('Has assessments')).toBeInTheDocument()
    expect(screen.getByText('At least 2 objectives found')).toBeInTheDocument()
  })

  it('renders suggestions', () => {
    render(<PlanReport report={mockReport} score={85} />)
    expect(screen.getByText('Add more activities')).toBeInTheDocument()
    expect(screen.getByText('Include adaptations')).toBeInTheDocument()
  })

  it('renders passed/failed labels for structural checks', () => {
    render(<PlanReport report={mockReport} score={85} />)
    const passedLabels = screen.getAllByLabelText('quality.passed')
    const failedLabels = screen.getAllByLabelText('quality.failed')
    expect(passedLabels).toHaveLength(1)
    expect(failedLabels).toHaveLength(1)
  })

  it('uses report score when standalone score is null', () => {
    render(<PlanReport report={mockReport} score={null} />)
    const meter = screen.getByRole('meter')
    expect(meter).toHaveAttribute('aria-valuenow', '85')
  })

  it('does not render structural checks section when empty', () => {
    const reportNoChecks: QualityReport = {
      ...mockReport,
      structural_checks: [],
    }
    render(<PlanReport report={reportNoChecks} score={85} />)
    expect(screen.queryByText('quality.structural_checks')).not.toBeInTheDocument()
  })

  it('does not render suggestions section when empty', () => {
    const reportNoSuggestions: QualityReport = {
      ...mockReport,
      suggestions: [],
    }
    render(<PlanReport report={reportNoSuggestions} score={85} />)
    expect(screen.queryByText('quality.suggestions')).not.toBeInTheDocument()
  })
})
