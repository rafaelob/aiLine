import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StudentPlan } from './student-plan'
import type { StudyPlan } from '@/types/plan'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

const mockPlan: StudyPlan = {
  id: 'plan-1',
  title: 'Fracoes e Decimais',
  subject: 'Matematica',
  grade: '5o Ano',
  objectives: ['Learn fractions', 'Practice conversions'],
  activities: [
    {
      title: 'Discussion',
      description: 'Talk about fractions',
      duration_minutes: 15,
      materials: ['Whiteboard'],
      adaptations: [],
    },
    {
      title: 'Exercises',
      description: 'Hands-on work',
      duration_minutes: 25,
      materials: [],
      adaptations: [],
    },
  ],
  assessments: [],
  accessibility_notes: [],
  curriculum_alignment: [],
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
}

describe('StudentPlan', () => {
  it('renders the plan title', () => {
    render(<StudentPlan plan={mockPlan} />)
    expect(screen.getByText('Fracoes e Decimais')).toBeInTheDocument()
  })

  it('renders subject and grade', () => {
    render(<StudentPlan plan={mockPlan} />)
    expect(screen.getByText(/Matematica/)).toBeInTheDocument()
    expect(screen.getByText(/5o Ano/)).toBeInTheDocument()
  })

  it('renders objectives with "What You Will Learn" heading', () => {
    render(<StudentPlan plan={mockPlan} />)
    expect(screen.getByText('What You Will Learn')).toBeInTheDocument()
    expect(screen.getByText('Learn fractions')).toBeInTheDocument()
    expect(screen.getByText('Practice conversions')).toBeInTheDocument()
  })

  it('renders numbered objectives', () => {
    render(<StudentPlan plan={mockPlan} />)
    // Both objectives and activities have number badges, so multiple "1" and "2" exist
    const allOnes = screen.getAllByText('1')
    const allTwos = screen.getAllByText('2')
    expect(allOnes.length).toBeGreaterThanOrEqual(1)
    expect(allTwos.length).toBeGreaterThanOrEqual(1)
  })

  it('renders activities section', () => {
    render(<StudentPlan plan={mockPlan} />)
    expect(screen.getByText('Activities')).toBeInTheDocument()
    expect(screen.getByText('Discussion')).toBeInTheDocument()
    expect(screen.getByText('Exercises')).toBeInTheDocument()
  })

  it('displays activity durations', () => {
    render(<StudentPlan plan={mockPlan} />)
    expect(screen.getByText('15 minutes')).toBeInTheDocument()
    expect(screen.getByText('25 minutes')).toBeInTheDocument()
  })

  it('has accessible article label', () => {
    render(<StudentPlan plan={mockPlan} />)
    const article = screen.getByLabelText(/Student plan: Fracoes e Decimais/)
    expect(article).toBeInTheDocument()
  })

  it('uses centered header layout', () => {
    render(<StudentPlan plan={mockPlan} />)
    const header = screen.getByText('Fracoes e Decimais').closest('header')
    expect(header).toHaveClass('text-center')
  })
})
