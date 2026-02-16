import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingStats } from './landing-stats'

vi.mock('@/components/shared/animated-counter', () => ({
  AnimatedCounter: ({ value, suffix, label }: { value: number; suffix: string; label?: string }) => (
    <span data-testid={`counter-${label}`}>{value}{suffix}</span>
  ),
}))

const defaultProps = {
  personas: 'Personas',
  languages: 'Languages',
  models: 'Models',
  standards: 'Standards',
  sectionLabel: 'Key Statistics',
}

describe('LandingStats', () => {
  it('renders without crashing', () => {
    const { container } = render(<LandingStats {...defaultProps} />)
    expect(container.querySelector('section')).toBeInTheDocument()
  })

  it('section has accessible aria-label', () => {
    const { container } = render(<LandingStats {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section).toHaveAttribute('aria-label', 'Key Statistics')
  })

  it('renders all 4 stat labels', () => {
    render(<LandingStats {...defaultProps} />)
    expect(screen.getByText('Personas')).toBeInTheDocument()
    expect(screen.getByText('Languages')).toBeInTheDocument()
    expect(screen.getByText('Models')).toBeInTheDocument()
    expect(screen.getByText('Standards')).toBeInTheDocument()
  })

  it('renders animated counters with correct values', () => {
    render(<LandingStats {...defaultProps} />)
    expect(screen.getByTestId('counter-Personas')).toHaveTextContent('9+')
    expect(screen.getByTestId('counter-Languages')).toHaveTextContent('3+')
    expect(screen.getByTestId('counter-Models')).toHaveTextContent('5+')
    expect(screen.getByTestId('counter-Standards')).toHaveTextContent('3+')
  })

  it('uses responsive 4-column grid', () => {
    const { container } = render(<LandingStats {...defaultProps} />)
    const grid = container.querySelector('.grid')
    expect(grid).toBeInTheDocument()
    expect(grid?.className).toContain('grid-cols-2')
    expect(grid?.className).toContain('sm:grid-cols-4')
  })

  it('stat items have centered flex layout', () => {
    const { container } = render(<LandingStats {...defaultProps} />)
    const statItems = container.querySelectorAll('.flex.flex-col.items-center')
    expect(statItems.length).toBe(4)
  })
})
