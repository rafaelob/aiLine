import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LearningTrajectory } from './learning-trajectory'

const MOCK_DATA = [
  { date: '2026-02-01', score: 65 },
  { date: '2026-02-08', score: 72 },
  { date: '2026-02-15', score: 80 },
]

const MULTI_SUBJECT_DATA = [
  { date: '2026-02-01', score: 65, subject: 'Math' },
  { date: '2026-02-01', score: 70, subject: 'Science' },
  { date: '2026-02-08', score: 72, subject: 'Math' },
  { date: '2026-02-08', score: 78, subject: 'Science' },
]

describe('LearningTrajectory', () => {
  it('renders nothing with empty data', () => {
    const { container } = render(<LearningTrajectory data={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders chart with role="figure" and summary', () => {
    render(<LearningTrajectory data={MOCK_DATA} />)
    const figure = screen.getByRole('figure')
    expect(figure).toHaveAttribute('aria-label')
    expect(figure.getAttribute('aria-label')).toContain('3 data points')
    expect(figure.getAttribute('aria-label')).toContain('average score 72')
  })

  it('renders sr-only data table', () => {
    render(<LearningTrajectory data={MOCK_DATA} />)
    const table = screen.getByRole('table')
    expect(table).toBeInTheDocument()
    expect(table).toHaveClass('sr-only')
  })

  it('renders heading', () => {
    render(<LearningTrajectory data={MOCK_DATA} />)
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument()
  })

  it('handles multi-subject data', () => {
    render(
      <LearningTrajectory
        data={MULTI_SUBJECT_DATA}
        subjects={['Math', 'Science']}
      />,
    )
    const figure = screen.getByRole('figure')
    expect(figure).toHaveAttribute('aria-label')
    expect(figure.getAttribute('aria-label')).toContain('4 data points')
  })
})
