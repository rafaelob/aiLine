import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingHowItWorks } from './landing-how-it-works'

vi.mock('motion/react', () => ({
  motion: {
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  useInView: () => true,
  useReducedMotion: () => false,
}))

const defaultProps = {
  title: 'How It Works',
  steps: [
    { title: 'Choose a Role', description: 'Log in as Teacher or Student' },
    { title: 'Create Plans', description: 'Teachers create AI-powered plans' },
    { title: 'AI Adapts', description: 'Content adapts for accessibility' },
    { title: 'Track Progress', description: 'Monitor and improve' },
  ],
}

describe('LandingHowItWorks', () => {
  it('renders without crashing', () => {
    render(<LandingHowItWorks {...defaultProps} />)
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument()
  })

  it('renders the section title', () => {
    render(<LandingHowItWorks {...defaultProps} />)
    expect(screen.getByText('How It Works')).toBeInTheDocument()
  })

  it('renders all 4 step cards', () => {
    render(<LandingHowItWorks {...defaultProps} />)
    expect(screen.getByText('Choose a Role')).toBeInTheDocument()
    expect(screen.getByText('Create Plans')).toBeInTheDocument()
    expect(screen.getByText('AI Adapts')).toBeInTheDocument()
    expect(screen.getByText('Track Progress')).toBeInTheDocument()
  })

  it('renders step descriptions', () => {
    render(<LandingHowItWorks {...defaultProps} />)
    expect(screen.getByText('Log in as Teacher or Student')).toBeInTheDocument()
    expect(screen.getByText('Content adapts for accessibility')).toBeInTheDocument()
  })

  it('section has aria-labelledby pointing to heading', () => {
    const { container } = render(<LandingHowItWorks {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section).toHaveAttribute('aria-labelledby', 'how-it-works-heading')
  })

  it('heading has correct id', () => {
    render(<LandingHowItWorks {...defaultProps} />)
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toHaveAttribute('id', 'how-it-works-heading')
  })

  it('renders step number indicators', () => {
    const { container } = render(<LandingHowItWorks {...defaultProps} />)
    const numbers = container.querySelectorAll('[aria-hidden="true"]')
    // Each step has: step number div + icon container, so at least 4 step numbers
    expect(numbers.length).toBeGreaterThanOrEqual(4)
  })
})
