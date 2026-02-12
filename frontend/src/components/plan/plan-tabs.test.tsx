import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PlanTabs } from './plan-tabs'
import type { StudyPlan } from '@/types/plan'

vi.mock('./teacher-plan', () => ({
  TeacherPlan: () => <div data-testid="teacher-plan">Teacher Plan</div>,
}))
vi.mock('./student-plan', () => ({
  StudentPlan: () => <div data-testid="student-plan">Student Plan</div>,
}))
vi.mock('./plan-report', () => ({
  PlanReport: () => <div data-testid="plan-report">Plan Report</div>,
}))
vi.mock('./plan-exports', () => ({
  PlanExports: () => <div data-testid="plan-exports">Plan Exports</div>,
}))
vi.mock('./session-summary', () => ({
  SessionSummary: () => <div data-testid="session-summary">Session Summary</div>,
}))

const mockPlan: StudyPlan = {
  id: 'plan-1',
  title: 'Test Plan',
  subject: 'Math',
  grade: '5th',
  objectives: ['Learn fractions'],
  activities: [],
  assessments: [],
  accessibility_notes: [],
  curriculum_alignment: [],
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
}

describe('PlanTabs', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders a tablist', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const tablist = screen.getByRole('tablist')
    expect(tablist).toBeInTheDocument()
  })

  it('renders 5 tabs', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const tabs = screen.getAllByRole('tab')
    expect(tabs).toHaveLength(5)
  })

  it('shows teacher tab as active by default', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const teacherTab = screen.getByRole('tab', { name: 'plans.tabs.teacher' })
    expect(teacherTab).toHaveAttribute('aria-selected', 'true')
  })

  it('renders teacher plan content by default', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    expect(screen.getByTestId('teacher-plan')).toBeInTheDocument()
  })

  it('switches to student tab on click', async () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const studentTab = screen.getByRole('tab', { name: 'plans.tabs.student' })
    await user.click(studentTab)

    expect(studentTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByTestId('student-plan')).toBeInTheDocument()
  })

  it('switches to report tab on click', async () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const reportTab = screen.getByRole('tab', { name: 'plans.tabs.report' })
    await user.click(reportTab)

    expect(screen.getByTestId('plan-report')).toBeInTheDocument()
  })

  it('switches to exports tab on click', async () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const exportsTab = screen.getByRole('tab', { name: 'plans.tabs.exports' })
    await user.click(exportsTab)

    expect(screen.getByTestId('plan-exports')).toBeInTheDocument()
  })

  it('has proper ARIA controls attributes on tabs', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const teacherTab = screen.getByRole('tab', { name: 'plans.tabs.teacher' })
    expect(teacherTab).toHaveAttribute('aria-controls', 'tabpanel-teacher')
  })

  it('inactive tabs have tabIndex -1', () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const studentTab = screen.getByRole('tab', { name: 'plans.tabs.student' })
    expect(studentTab).toHaveAttribute('tabindex', '-1')
  })

  it('supports keyboard navigation with ArrowRight', async () => {
    render(<PlanTabs plan={mockPlan} qualityReport={null} score={null} />)
    const teacherTab = screen.getByRole('tab', { name: 'plans.tabs.teacher' })
    teacherTab.focus()
    await user.keyboard('{ArrowRight}')

    const studentTab = screen.getByRole('tab', { name: 'plans.tabs.student' })
    expect(studentTab).toHaveAttribute('aria-selected', 'true')
  })
})
