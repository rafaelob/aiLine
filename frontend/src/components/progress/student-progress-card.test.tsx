import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StudentProgressCard } from './student-progress-card'

// Mock motion/react to render static elements
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

function makeStudent(overrides: Record<string, unknown> = {}) {
  return {
    student_id: 'stu-001',
    student_name: 'Maria Silva',
    standards_count: 10,
    mastered_count: 6,
    proficient_count: 2,
    developing_count: 2,
    last_activity: '2026-02-14T10:30:00Z',
    ...overrides,
  }
}

describe('StudentProgressCard', () => {
  it('renders the student name', () => {
    render(<StudentProgressCard student={makeStudent()} />)
    expect(screen.getByText('Maria Silva')).toBeInTheDocument()
  })

  it('falls back to student_id when name is empty', () => {
    render(<StudentProgressCard student={makeStudent({ student_name: '' })} />)
    expect(screen.getByText('stu-001')).toBeInTheDocument()
  })

  it('shows the mastery percentage', () => {
    // 6 mastered out of 10 = 60%
    render(<StudentProgressCard student={makeStudent()} />)
    // 60% appears multiple times (badge + progress bar label)
    const percentLabels = screen.getAllByText('60%')
    expect(percentLabels.length).toBeGreaterThan(0)
  })

  it('calculates 100% when all standards are mastered', () => {
    render(
      <StudentProgressCard
        student={makeStudent({
          standards_count: 5,
          mastered_count: 5,
          proficient_count: 0,
          developing_count: 0,
        })}
      />
    )
    // 100% appears in badge and progress bar label
    const percentLabels = screen.getAllByText('100%')
    expect(percentLabels.length).toBeGreaterThan(0)
  })

  it('shows 0% when no standards are mastered', () => {
    render(
      <StudentProgressCard
        student={makeStudent({
          mastered_count: 0,
          proficient_count: 3,
          developing_count: 7,
        })}
      />
    )
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('renders progress sections for mastered, proficient, and developing', () => {
    const { container } = render(<StudentProgressCard student={makeStudent()} />)

    // The card now renders individual progress bars with labels
    // Each progress bar is in a flex container with h-1.5
    const progressBars = container.querySelectorAll('.h-1\\.5.rounded-full.overflow-hidden')
    expect(progressBars.length).toBe(3) // mastered, proficient, developing
  })

  it('displays correct percentage labels', () => {
    render(<StudentProgressCard student={makeStudent()} />)

    // mastered: 6/10 = 60%, proficient: 2/10 = 20%, developing: 2/10 = 20%
    // The percentages are now shown as text labels at the end of each row
    const percentLabels = screen.getAllByText(/\d+%/)

    // Main percentage badge (60%) + 3 progress bar labels (60%, 20%, 20%)
    expect(percentLabels.length).toBeGreaterThanOrEqual(4)

    // Check for the main mastery percentage in the badge (appears twice: badge + bar)
    const masteryLabels = screen.getAllByText('60%')
    expect(masteryLabels.length).toBeGreaterThan(0)
  })

  it('omits progress section when count is zero', () => {
    const { container } = render(
      <StudentProgressCard
        student={makeStudent({
          mastered_count: 5,
          proficient_count: 0,
          developing_count: 5,
        })}
      />
    )

    const progressBars = container.querySelectorAll('.h-1\\.5.rounded-full.overflow-hidden')
    // proficient is 0, so only mastered + developing sections render
    expect(progressBars.length).toBe(2)
  })

  it('shows last activity date when present', () => {
    render(<StudentProgressCard student={makeStudent()} />)
    // The component formats the date with toLocaleDateString()
    const formatted = new Date('2026-02-14T10:30:00Z').toLocaleDateString()
    expect(screen.getByText(`progress.last_activity: ${formatted}`)).toBeInTheDocument()
  })

  it('does not show last activity when null', () => {
    render(
      <StudentProgressCard student={makeStudent({ last_activity: null })} />
    )
    expect(screen.queryByText(/progress\.last_activity/)).not.toBeInTheDocument()
  })

  it('displays the total standards count', () => {
    render(<StudentProgressCard student={makeStudent({ standards_count: 10 })} />)
    // The translated string: "10 progress.total_standards"
    expect(screen.getByText(/10/)).toBeInTheDocument()
    expect(screen.getByText(/progress\.total_standards/)).toBeInTheDocument()
  })

  it('handles edge case of zero standards_count without dividing by zero', () => {
    // When standards_count is 0, total becomes 1 (|| 1 guard)
    render(
      <StudentProgressCard
        student={makeStudent({
          standards_count: 0,
          mastered_count: 0,
          proficient_count: 0,
          developing_count: 0,
        })}
      />
    )
    expect(screen.getByText('0%')).toBeInTheDocument()
  })
})
