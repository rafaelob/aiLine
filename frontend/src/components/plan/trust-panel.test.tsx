import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrustPanel } from './trust-panel'
import type { QualityReport } from '@/types/plan'
import type { ScorecardData } from './transformation-scorecard'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, layout: _l, layoutId: _li, initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
    span: ({ children, layout: _l, layoutId: _li, initial: _i, animate: _a, exit: _e, transition: _t, style: _s, variants: _v, ...rest }: Record<string, unknown>) => {
      return <span {...rest}>{children as React.ReactNode}</span>
    },
  },
}))

const mockQualityReport: QualityReport = {
  score: 85,
  structural_checks: [
    { name: 'Has objectives', passed: true, message: 'ok' },
    { name: 'Has activities', passed: true, message: 'ok' },
    { name: 'Has assessments', passed: false, message: 'missing' },
  ],
  suggestions: ['Add more activities', 'Improve assessments'],
  decision: 'accept',
}

const mockScorecard: ScorecardData = {
  reading_level_before: 8,
  reading_level_after: 5,
  standards_aligned: [
    { code: 'BNCC-001', description: 'Standard 1' },
    { code: 'BNCC-002', description: 'Standard 2' },
  ],
  accessibility_adaptations: ['Large text', 'High contrast'],
  rag_groundedness: 0.82,
  quality_score: 85,
  quality_decision: 'accept',
  model_used: 'claude-opus-4-6',
  router_rationale: 'Best for structured output',
  time_saved_estimate: '2h 30m',
  total_pipeline_time_ms: 4500,
  export_variants_count: 7,
}

describe('TrustPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders empty state when no data', () => {
    render(
      <TrustPanel
        qualityReport={null}
        score={null}
        scorecard={null}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('trust.no_data')).toBeInTheDocument()
  })

  it('renders score when provided', () => {
    render(
      <TrustPanel
        qualityReport={null}
        score={92}
        scorecard={null}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('92')).toBeInTheDocument()
    expect(screen.getByText('/100')).toBeInTheDocument()
  })

  it('renders structural checks from quality report', () => {
    render(
      <TrustPanel
        qualityReport={mockQualityReport}
        score={85}
        scorecard={null}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('Has objectives')).toBeInTheDocument()
    expect(screen.getByText('Has activities')).toBeInTheDocument()
    expect(screen.getByText('Has assessments')).toBeInTheDocument()
  })

  it('renders scorecard metrics', () => {
    render(
      <TrustPanel
        qualityReport={null}
        score={null}
        scorecard={mockScorecard}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    // Standards count and adaptations count are both "2"
    expect(screen.getAllByText('2')).toHaveLength(2)
    // Pipeline time
    expect(screen.getByText('4.5s')).toBeInTheDocument()
    // Export variants
    expect(screen.getByText('7')).toBeInTheDocument()
    // RAG groundedness
    expect(screen.getByText('82%')).toBeInTheDocument()
  })

  it('renders model info from scorecard', () => {
    render(
      <TrustPanel
        qualityReport={null}
        score={null}
        scorecard={mockScorecard}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('trust.model_chosen')).toBeInTheDocument()
  })

  it('renders suggestions from quality report', () => {
    render(
      <TrustPanel
        qualityReport={mockQualityReport}
        score={85}
        scorecard={null}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('Add more activities')).toBeInTheDocument()
    expect(screen.getByText('Improve assessments')).toBeInTheDocument()
  })

  it('renders decision badge when accept', () => {
    render(
      <TrustPanel
        qualityReport={mockQualityReport}
        score={85}
        scorecard={null}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('Accepted')).toBeInTheDocument()
  })

  it('renders quality section heading', () => {
    render(
      <TrustPanel
        qualityReport={mockQualityReport}
        score={85}
        scorecard={mockScorecard}
        plan={{ id: 'p1', title: 'Test' }}
      />
    )
    expect(screen.getByText('trust.quality_section')).toBeInTheDocument()
    expect(screen.getByText('trust.standards_section')).toBeInTheDocument()
    expect(screen.getByText('trust.reasoning_section')).toBeInTheDocument()
  })
})
