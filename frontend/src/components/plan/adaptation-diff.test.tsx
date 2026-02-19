import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AdaptationDiff } from './adaptation-diff'
import type { StudyPlan } from '@/types/plan'

// Mock next-intl
vi.mock('next-intl', () => ({
  useTranslations: () => {
    const translations: Record<string, string> = {
      section_label: 'Adaptation comparison view',
      profile_tabs_label: 'Select accessibility profile to compare',
      'profiles.standard': 'Standard',
      'profiles.asd': 'ASD (Autism)',
      'profiles.adhd': 'ADHD',
      'profiles.dyslexia': 'Dyslexia',
      'profiles.hearing': 'Hearing',
      legend_label: 'Diff legend',
      legend_addition: 'Addition (new accommodation)',
      legend_modification: 'Modification (adapted content)',
      legend_removal: 'Removal (simplified away)',
      comparison_label: 'Side-by-side plan comparison',
      standard_title: 'Standard Plan',
      standard_content_label: 'Standard plan content',
      adapted_title: 'Adapted for test',
      adapted_content_label: 'Adapted plan content',
      summary: '1 additions, 1 modifications, 0 removals',
    }
    return (key: string, params?: Record<string, string>) => {
      if (params && key === 'adapted_title') return `Adapted for ${params.profile}`
      if (params && key === 'summary') {
        return `${params.additions} additions, ${params.modifications} modifications, ${params.removals} removals`
      }
      return translations[key] ?? key
    }
  },
}))

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    span: ({ children, ...props }: Record<string, unknown>) => {
      const { layoutId, animate, transition, ...safe } = props
      void layoutId; void animate; void transition
      return <span {...safe}>{children as React.ReactNode}</span>
    },
    div: ({ children, ...props }: Record<string, unknown>) => {
      const { initial, animate, exit, transition, ...safe } = props
      void initial; void animate; void exit; void transition
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    article: ({ children, ...props }: Record<string, unknown>) => {
      const { initial, animate, transition, layoutId, ...safe } = props
      void initial; void animate; void transition; void layoutId
      return <article {...safe}>{children as React.ReactNode}</article>
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
  objectives: ['Understand photosynthesis', 'Identify plant parts'],
  activities: [
    {
      title: 'Introduction Video',
      description: 'Watch a 5-minute video about photosynthesis',
      duration_minutes: 10,
      materials: ['Projector', 'Video file'],
      adaptations: [
        { profile: 'asd', description: 'Video with visual timer and calm background music' },
        { profile: 'adhd', description: 'Video split into 2-minute chunks with check-ins' },
        { profile: 'dyslexia', description: 'Video with highlighted key terms and slow narration' },
        { profile: 'hearing', description: 'Video with captions and sign language interpreter window' },
      ],
    },
    {
      title: 'Lab Activity',
      description: 'Hands-on plant observation experiment',
      duration_minutes: 20,
      materials: ['Plants', 'Magnifying glass'],
      adaptations: [
        { profile: 'asd', description: 'Step-by-step visual instructions with numbered cards' },
      ],
    },
  ],
  assessments: [
    {
      title: 'Quiz',
      type: 'Multiple Choice',
      criteria: ['Identify stages', 'Name reactants'],
      adaptations: [
        { profile: 'dyslexia', description: 'Larger font, fewer options per question' },
      ],
    },
  ],
  accessibility_notes: [
    'Visual schedule provided for ASD students',
    'Focus mode enabled for ADHD students',
  ],
  curriculum_alignment: [
    { standard_id: 'NGSS-LS1', standard_name: 'Life Science', description: 'Photosynthesis' },
  ],
  created_at: '2026-02-19T00:00:00Z',
  updated_at: '2026-02-19T00:00:00Z',
}

describe('AdaptationDiff', () => {
  it('renders the section with accessible label', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    expect(screen.getByLabelText('Adaptation comparison view')).toBeInTheDocument()
  })

  it('renders profile selector tabs with correct ARIA attributes', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    const tablist = screen.getByRole('tablist')
    expect(tablist).toHaveAttribute('aria-label', 'Select accessibility profile to compare')

    const tabs = within(tablist).getAllByRole('tab')
    expect(tabs).toHaveLength(4) // ASD, ADHD, Dyslexia, Hearing (no standard)
  })

  it('starts with ASD profile selected', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    const asdTab = screen.getByRole('tab', { name: 'ASD (Autism)' })
    expect(asdTab).toHaveAttribute('aria-selected', 'true')
  })

  it('switches profile on tab click', async () => {
    const user = userEvent.setup()
    render(<AdaptationDiff plan={MOCK_PLAN} />)

    const adhdTab = screen.getByRole('tab', { name: 'ADHD' })
    await user.click(adhdTab)
    expect(adhdTab).toHaveAttribute('aria-selected', 'true')

    // ASD should no longer be selected
    const asdTab = screen.getByRole('tab', { name: 'ASD (Autism)' })
    expect(asdTab).toHaveAttribute('aria-selected', 'false')
  })

  it('renders both standard and adapted panels', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    expect(screen.getByText('Standard Plan')).toBeInTheDocument()
    expect(screen.getByText(/Adapted for/)).toBeInTheDocument()
  })

  it('renders diff legend with three types', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    expect(screen.getByText('Addition (new accommodation)')).toBeInTheDocument()
    expect(screen.getByText('Modification (adapted content)')).toBeInTheDocument()
    expect(screen.getByText('Removal (simplified away)')).toBeInTheDocument()
  })

  it('renders plan activities in the standard panel', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    expect(screen.getAllByText('Introduction Video').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Lab Activity').length).toBeGreaterThanOrEqual(1)
  })

  it('renders summary with diff counts', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    const summary = screen.getByText(/additions,.*modifications,.*removals/)
    expect(summary).toBeInTheDocument()
  })

  it('renders the side-by-side comparison region', () => {
    render(<AdaptationDiff plan={MOCK_PLAN} />)
    expect(screen.getByLabelText('Side-by-side plan comparison')).toBeInTheDocument()
  })
})
