import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressOverview } from './progress-overview'

const MOCK_DATA = [
  { topic: 'Fractions', mastered: 5, proficient: 3, developing: 2, not_started: 1 },
  { topic: 'Geometry', mastered: 2, proficient: 4, developing: 3, not_started: 2 },
]

describe('ProgressOverview', () => {
  it('renders nothing with empty data', () => {
    const { container } = render(<ProgressOverview data={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders chart with role="figure" and aria-label', () => {
    render(<ProgressOverview data={MOCK_DATA} />)
    const figure = screen.getByRole('figure')
    expect(figure).toHaveAttribute('aria-label')
    expect(figure.getAttribute('aria-label')).toContain('2 topics')
  })

  it('renders sr-only data table for screen readers', () => {
    render(<ProgressOverview data={MOCK_DATA} />)
    // The sr-only table should have the data
    const table = screen.getByRole('table')
    expect(table).toBeInTheDocument()
    expect(table).toHaveClass('sr-only')
  })

  it('shows mastery data in sr-only table cells', () => {
    render(<ProgressOverview data={MOCK_DATA} />)
    // Fractions topic should appear in the table
    expect(screen.getByText('Fractions')).toBeInTheDocument()
    expect(screen.getByText('Geometry')).toBeInTheDocument()
  })

  it('renders heading with dashboard title', () => {
    render(<ProgressOverview data={MOCK_DATA} />)
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument()
  })
})
