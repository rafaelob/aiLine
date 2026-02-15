import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TransformationScorecard, type ScorecardData } from './transformation-scorecard'

// Mock motion/react to render static elements
vi.mock('motion/react', () => ({
  motion: {
    section: ({ children, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <section {...rest}>{children as React.ReactNode}</section>
    },
    div: ({ children, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
}))

function makeScorecardData(overrides: Partial<ScorecardData> = {}): ScorecardData {
  return {
    reading_level_before: 8.5,
    reading_level_after: 5.2,
    standards_aligned: [
      { code: 'EF06MA01', description: 'Understand fractions' },
      { code: 'EF06MA02', description: 'Operate with decimals' },
    ],
    accessibility_adaptations: ['autism: visual schedule', 'adhd: short instructions'],
    rag_groundedness: 0.85,
    quality_score: 92,
    quality_decision: 'accept',
    model_used: 'claude-haiku-4-5-20251001',
    router_rationale: 'Low token count',
    time_saved_estimate: '~30 min -> 12s',
    total_pipeline_time_ms: 12345,
    export_variants_count: 10,
    ...overrides,
  }
}

describe('TransformationScorecard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the section with an aria-label', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    const section = screen.getByRole('region', { name: 'scorecard.title' })
    expect(section).toBeInTheDocument()
  })

  it('renders all metric labels', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('scorecard.quality_score')).toBeInTheDocument()
    expect(screen.getByText('scorecard.time_saved')).toBeInTheDocument()
    expect(screen.getByText('scorecard.reading_level')).toBeInTheDocument()
    expect(screen.getByText('scorecard.rag_groundedness')).toBeInTheDocument()
    expect(screen.getByText('scorecard.standards_aligned')).toBeInTheDocument()
    expect(screen.getByText('scorecard.accessibility')).toBeInTheDocument()
    expect(screen.getByText('scorecard.model_used')).toBeInTheDocument()
    expect(screen.getByText('scorecard.pipeline_time')).toBeInTheDocument()
    expect(screen.getByText('scorecard.export_variants')).toBeInTheDocument()
  })

  it('displays quality score value', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ quality_score: 92 })} />)
    expect(screen.getByText('92')).toBeInTheDocument()
    expect(screen.getByText('/100')).toBeInTheDocument()
  })

  it('displays quality decision badge', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ quality_decision: 'accept' })} />)
    expect(screen.getByText('accept')).toBeInTheDocument()
  })

  it('displays time saved estimate', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('~30 min -> 12s')).toBeInTheDocument()
  })

  it('displays reading levels (before and after)', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('8.5')).toBeInTheDocument()
    expect(screen.getByText('5.2')).toBeInTheDocument()
    expect(screen.getByText('scorecard.before')).toBeInTheDocument()
    expect(screen.getByText('scorecard.after')).toBeInTheDocument()
  })

  it('displays RAG groundedness percentage', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ rag_groundedness: 0.85 })} />)
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('displays standards badges', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('EF06MA01')).toBeInTheDocument()
    expect(screen.getByText('EF06MA02')).toBeInTheDocument()
  })

  it('shows dash when no standards aligned', () => {
    render(
      <TransformationScorecard
        scorecard={makeScorecardData({ standards_aligned: [] })}
      />
    )
    // The dash character for empty standards
    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThanOrEqual(1)
  })

  it('displays accessibility adaptation tags', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('autism: visual schedule')).toBeInTheDocument()
    expect(screen.getByText('adhd: short instructions')).toBeInTheDocument()
  })

  it('shows dash when no accessibility adaptations', () => {
    render(
      <TransformationScorecard
        scorecard={makeScorecardData({ accessibility_adaptations: [] })}
      />
    )
    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThanOrEqual(1)
  })

  it('displays model name', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('claude-haiku-4-5-20251001')).toBeInTheDocument()
  })

  it('shows "Auto" when model_used is empty', () => {
    render(
      <TransformationScorecard
        scorecard={makeScorecardData({ model_used: '' })}
      />
    )
    expect(screen.getByText('Auto')).toBeInTheDocument()
  })

  it('displays router rationale when present', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('Low token count')).toBeInTheDocument()
  })

  it('displays pipeline time in seconds', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ total_pipeline_time_ms: 12345 })} />)
    expect(screen.getByText('12.3s')).toBeInTheDocument()
  })

  it('displays export variants count', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ export_variants_count: 10 })} />)
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('displays header with title', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('scorecard.title')).toBeInTheDocument()
  })

  it('displays powered by text', () => {
    render(<TransformationScorecard scorecard={makeScorecardData()} />)
    expect(screen.getByText('Powered by Claude Opus 4.6')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <TransformationScorecard scorecard={makeScorecardData()} className="custom-class" />
    )
    const section = container.querySelector('section')
    expect(section?.className).toContain('custom-class')
  })

  it('quality score >= 80 uses success color', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ quality_score: 85 })} />)
    const scoreElement = screen.getByText('85')
    expect(scoreElement).toHaveStyle({ color: 'var(--color-success)' })
  })

  it('quality score between 60-79 uses warning color', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ quality_score: 70 })} />)
    const scoreElement = screen.getByText('70')
    expect(scoreElement).toHaveStyle({ color: 'var(--color-warning)' })
  })

  it('quality score below 60 uses error color', () => {
    render(<TransformationScorecard scorecard={makeScorecardData({ quality_score: 45 })} />)
    const scoreElement = screen.getByText('45')
    expect(scoreElement).toHaveStyle({ color: 'var(--color-error)' })
  })
})
