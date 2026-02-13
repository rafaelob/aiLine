import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TeacherPlan } from './teacher-plan'
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
  objectives: ['Learn fractions', 'Convert decimals'],
  activities: [
    {
      title: 'Roda de Conversa',
      description: 'Discuss fractions in daily life',
      duration_minutes: 15,
      materials: ['Whiteboard', 'Markers'],
      adaptations: [
        { profile: 'TEA', description: 'Use visual images' },
      ],
    },
    {
      title: 'Practice',
      description: 'Hands-on exercises',
      duration_minutes: 25,
      materials: [],
      adaptations: [],
    },
  ],
  assessments: [
    {
      title: 'Quick Quiz',
      type: 'formative',
      criteria: ['Understands fractions', 'Can convert'],
      adaptations: [],
    },
  ],
  accessibility_notes: ['Use large fonts for low vision students'],
  curriculum_alignment: [],
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
}

describe('TeacherPlan', () => {
  it('renders the plan title', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Fracoes e Decimais')).toBeInTheDocument()
  })

  it('renders subject and grade', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Matematica')).toBeInTheDocument()
    expect(screen.getByText('5o Ano')).toBeInTheDocument()
  })

  it('renders all objectives', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Learn fractions')).toBeInTheDocument()
    expect(screen.getByText('Convert decimals')).toBeInTheDocument()
  })

  it('renders activities with titles and descriptions', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Roda de Conversa')).toBeInTheDocument()
    expect(screen.getByText('Discuss fractions in daily life')).toBeInTheDocument()
    expect(screen.getByText('Practice')).toBeInTheDocument()
  })

  it('renders activity duration', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('15 min')).toBeInTheDocument()
    expect(screen.getByText('25 min')).toBeInTheDocument()
  })

  it('renders materials when present', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Whiteboard')).toBeInTheDocument()
    expect(screen.getByText('Markers')).toBeInTheDocument()
  })

  it('renders adaptations when present', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('[TEA]')).toBeInTheDocument()
    expect(screen.getByText('Use visual images')).toBeInTheDocument()
  })

  it('renders assessments', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(screen.getByText('Quick Quiz')).toBeInTheDocument()
    expect(screen.getByText('teacher_plan.type: formative')).toBeInTheDocument()
    expect(screen.getByText('Understands fractions')).toBeInTheDocument()
  })

  it('renders accessibility notes', () => {
    render(<TeacherPlan plan={mockPlan} />)
    expect(
      screen.getByText('Use large fonts for low vision students')
    ).toBeInTheDocument()
  })

  it('has accessible article label', () => {
    render(<TeacherPlan plan={mockPlan} />)
    const article = screen.getByLabelText('Fracoes e Decimais')
    expect(article).toBeInTheDocument()
  })

  it('does not render assessments section when empty', () => {
    const planNoAssessments = { ...mockPlan, assessments: [] }
    render(<TeacherPlan plan={planNoAssessments} />)
    expect(screen.queryByText('teacher_plan.assessments')).not.toBeInTheDocument()
  })

  it('does not render accessibility notes section when empty', () => {
    const planNoNotes = { ...mockPlan, accessibility_notes: [] }
    render(<TeacherPlan plan={planNoNotes} />)
    expect(screen.queryByText('teacher_plan.accessibility_notes')).not.toBeInTheDocument()
  })
})
