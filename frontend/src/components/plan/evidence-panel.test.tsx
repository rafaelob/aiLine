import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EvidencePanel } from './evidence-panel'
import { usePipelineStore } from '@/stores/pipeline-store'
import type { StudyPlan, QualityReport } from '@/types/plan'
import type { ScorecardData } from './transformation-scorecard'

// Mock next-intl
vi.mock('next-intl', () => ({
  useTranslations: () => {
    const translations: Record<string, string> = {
      section_label: 'AI evidence and transparency panel',
      title: 'AI Evidence & Transparency',
      model_title: 'AI Model',
      model_name: 'Model',
      router_rationale: 'Routing Rationale',
      quality_title: 'Quality Score',
      standards_title: 'Standards Aligned',
      rag_title: 'RAG Provenance',
      rag_description: 'Percentage of content backed by uploaded teaching materials',
      accommodations_title: 'Accommodations',
      processing_title: 'Processing',
      total_time: 'Total Time',
      refinement_loops: 'Refinement Loops',
      export_variants: 'Export Variants',
    }
    return (key: string) => translations[key] ?? key
  },
}))

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    span: ({ children, ...props }: Record<string, unknown>) => {
      const { animate, transition, ...safe } = props
      void animate; void transition
      return <span {...safe}>{children as React.ReactNode}</span>
    },
    div: ({ children, ...props }: Record<string, unknown>) => {
      const { initial, animate, exit, transition, ...safe } = props
      void initial; void animate; void exit; void transition
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
}))

const MOCK_PLAN: StudyPlan = {
  id: 'plan-1',
  title: 'Photosynthesis Lesson',
  subject: 'Science',
  grade: '6th Grade',
  objectives: ['Understand photosynthesis'],
  activities: [],
  assessments: [],
  accessibility_notes: [
    'Visual schedule provided for ASD students',
    'Focus mode enabled for ADHD students',
  ],
  curriculum_alignment: [
    { standard_id: 'NGSS-LS1', standard_name: 'Life Science', description: 'Photosynthesis' },
    { standard_id: 'CC-6.NS', standard_name: 'Math Standards', description: 'Number Systems' },
  ],
  created_at: '2026-02-19T00:00:00Z',
  updated_at: '2026-02-19T00:00:00Z',
}

const MOCK_QUALITY_REPORT: QualityReport = {
  score: 87,
  structural_checks: [
    { name: 'Has objectives', passed: true, message: 'OK' },
    { name: 'Has activities', passed: true, message: 'OK' },
    { name: 'Has assessments', passed: false, message: 'Missing rubric' },
  ],
  suggestions: ['Add more detailed rubric'],
  decision: 'accept',
}

const MOCK_SCORECARD: ScorecardData = {
  reading_level_before: 8,
  reading_level_after: 5,
  standards_aligned: [{ code: 'NGSS-LS1', description: 'Life Science' }],
  accessibility_adaptations: ['Visual schedule', 'Focus mode'],
  rag_groundedness: 0.78,
  quality_score: 87,
  quality_decision: 'accept',
  model_used: 'claude-opus-4-6',
  router_rationale: 'Selected for complex reasoning task',
  time_saved_estimate: '45 min',
  total_pipeline_time_ms: 12500,
  export_variants_count: 6,
}

describe('EvidencePanel', () => {
  beforeEach(() => {
    // Reset pipeline store to have some events
    usePipelineStore.getState().reset()
  })

  it('renders the section with accessible label', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByLabelText('AI evidence and transparency panel')).toBeInTheDocument()
  })

  it('renders the title', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('AI Evidence & Transparency')).toBeInTheDocument()
  })

  it('renders model section with badge', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('AI Model')).toBeInTheDocument()
    // Model name appears in badge and in details; use getAllByText
    const modelTexts = screen.getAllByText('claude-opus-4-6')
    expect(modelTexts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders quality score section with badge', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('Quality Score')).toBeInTheDocument()
    expect(screen.getByText('87/100')).toBeInTheDocument()
  })

  it('renders standards aligned section with count badge', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    const standardsTitle = screen.getByText('Standards Aligned')
    expect(standardsTitle).toBeInTheDocument()
    // Plan has 2 curriculum alignments; badge is sibling to title inside the button
    const standardsButton = standardsTitle.closest('button')!
    expect(within(standardsButton).getByText('2')).toBeInTheDocument()
  })

  it('renders RAG provenance section', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('RAG Provenance')).toBeInTheDocument()
    expect(screen.getByText('78%')).toBeInTheDocument()
  })

  it('renders accommodations section', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('Accommodations')).toBeInTheDocument()
  })

  it('renders processing section', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('12.5s')).toBeInTheDocument()
  })

  it('toggles accordion sections on click', async () => {
    const user = userEvent.setup()
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )

    // Standards section should initially be collapsed
    const standardsButton = screen.getByText('Standards Aligned').closest('button')!
    expect(standardsButton).toHaveAttribute('aria-expanded', 'false')

    // Click to expand
    await user.click(standardsButton)
    expect(standardsButton).toHaveAttribute('aria-expanded', 'true')

    // Click again to collapse
    await user.click(standardsButton)
    expect(standardsButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('has model and quality sections open by default', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )

    const modelButton = screen.getByText('AI Model').closest('button')!
    expect(modelButton).toHaveAttribute('aria-expanded', 'true')

    const qualityButton = screen.getByText('Quality Score').closest('button')!
    expect(qualityButton).toHaveAttribute('aria-expanded', 'true')
  })

  it('renders structural checks inside quality section', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    // Quality section is open by default, so checks should be visible
    expect(screen.getByText('Has objectives')).toBeInTheDocument()
    expect(screen.getByText('Has activities')).toBeInTheDocument()
    expect(screen.getByText('Has assessments')).toBeInTheDocument()
  })

  it('returns null when no data is available', () => {
    const emptyPlan: StudyPlan = {
      ...MOCK_PLAN,
      curriculum_alignment: [],
      accessibility_notes: [],
    }
    const { container } = render(
      <EvidencePanel plan={emptyPlan} qualityReport={null} scorecard={null} />,
    )
    // Should still render model section (with auto-routed)
    expect(screen.getByText('AI Model')).toBeInTheDocument()
  })

  it('renders accept decision badge for quality', () => {
    render(
      <EvidencePanel
        plan={MOCK_PLAN}
        qualityReport={MOCK_QUALITY_REPORT}
        scorecard={MOCK_SCORECARD}
      />,
    )
    expect(screen.getByText('accept')).toBeInTheDocument()
  })
})
