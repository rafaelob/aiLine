import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressHeatmap } from './progress-heatmap'

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    tr: ({ children, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <tr {...rest}>{children as React.ReactNode}</tr>
    },
  },
}))

function makeStandards() {
  return [
    {
      standard_code: 'EF06MA01',
      standard_description: 'Understand fractions',
      student_count: 10,
      mastered_count: 4,
      proficient_count: 3,
      developing_count: 3,
    },
    {
      standard_code: 'EF06MA02',
      standard_description: 'Operate with decimals',
      student_count: 8,
      mastered_count: 2,
      proficient_count: 4,
      developing_count: 2,
    },
  ]
}

describe('ProgressHeatmap', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the section title', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    expect(screen.getByText('progress.standards_heatmap')).toBeInTheDocument()
  })

  it('renders a table with grid role', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    expect(screen.getByRole('grid')).toBeInTheDocument()
  })

  it('renders column headers', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    expect(screen.getByText('Standard')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.mastered')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.proficient')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.developing')).toBeInTheDocument()
    expect(screen.getByText('Total')).toBeInTheDocument()
  })

  it('renders standard codes', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    expect(screen.getByText('EF06MA01')).toBeInTheDocument()
    expect(screen.getByText('EF06MA02')).toBeInTheDocument()
  })

  it('renders standard descriptions', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    expect(screen.getByText('Understand fractions')).toBeInTheDocument()
    expect(screen.getByText('Operate with decimals')).toBeInTheDocument()
  })

  it('renders mastery count values in heat cells', () => {
    render(<ProgressHeatmap standards={makeStandards()} />)
    // EF06MA01: mastered=4, proficient=3, developing=3, total=10
    // "4" appears in both EF06MA01 mastered and EF06MA02 proficient, so use getAllByText
    const fours = screen.getAllByText('4')
    expect(fours.length).toBeGreaterThanOrEqual(1)
    // Total columns: 10 and 8 are unique
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('renders correct number of rows', () => {
    const { container } = render(<ProgressHeatmap standards={makeStandards()} />)
    const rows = container.querySelectorAll('tbody tr')
    expect(rows.length).toBe(2)
  })

  it('renders empty table when no standards', () => {
    const { container } = render(<ProgressHeatmap standards={[]} />)
    const rows = container.querySelectorAll('tbody tr')
    expect(rows.length).toBe(0)
    // Header should still be present
    expect(screen.getByText('Standard')).toBeInTheDocument()
  })

  it('handles standard with no description', () => {
    const standards = [{
      standard_code: 'C1',
      standard_description: '',
      student_count: 5,
      mastered_count: 2,
      proficient_count: 2,
      developing_count: 1,
    }]
    const { container } = render(<ProgressHeatmap standards={standards} />)
    expect(screen.getByText('C1')).toBeInTheDocument()
    // No description element rendered for empty descriptions
    // (conditional render: s.standard_description && <div>...)
    const descDivs = container.querySelectorAll('.truncate.max-w-\\[200px\\]')
    expect(descDivs.length).toBe(0)
  })

  it('handles standard with zero students', () => {
    const standards = [{
      standard_code: 'C2',
      standard_description: 'Empty',
      student_count: 0,
      mastered_count: 0,
      proficient_count: 0,
      developing_count: 0,
    }]
    render(<ProgressHeatmap standards={standards} />)
    expect(screen.getByText('C2')).toBeInTheDocument()
    // Should not crash on division by zero (uses || 1)
  })
})
