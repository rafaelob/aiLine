import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingHero } from './landing-hero'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    h1: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <h1 {...safe}>{children as React.ReactNode}</h1>
    },
    p: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <p {...safe}>{children as React.ReactNode}</p>
    },
  },
  useReducedMotion: () => false,
}))

vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: Record<string, unknown>) => (
    <a href={href as string} {...rest}>{children as React.ReactNode}</a>
  ),
}))

const defaultProps = {
  locale: 'en',
  title: 'AI for Education',
  subtitle: 'Inclusive learning for everyone',
  cta: 'Start Demo',
}

describe('LandingHero', () => {
  it('renders without crashing', () => {
    render(<LandingHero {...defaultProps} />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('renders the title in an h1', () => {
    render(<LandingHero {...defaultProps} />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading.textContent).toBe('AI for Education')
  })

  it('renders the subtitle', () => {
    render(<LandingHero {...defaultProps} />)
    expect(screen.getByText('Inclusive learning for everyone')).toBeInTheDocument()
  })

  it('renders the CTA link', () => {
    render(<LandingHero {...defaultProps} />)
    const link = screen.getByRole('link')
    expect(link.textContent).toContain('Start Demo')
  })

  it('CTA link navigates to dashboard with locale prefix', () => {
    render(<LandingHero {...defaultProps} />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/en/dashboard')
  })

  it('section has aria-labelledby pointing to hero-heading', () => {
    const { container } = render(<LandingHero {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section).toHaveAttribute('aria-labelledby', 'hero-heading')
  })

  it('heading has id="hero-heading"', () => {
    render(<LandingHero {...defaultProps} />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveAttribute('id', 'hero-heading')
  })

  it('decorative elements are hidden from assistive tech', () => {
    const { container } = render(<LandingHero {...defaultProps} />)
    const decorativeElements = container.querySelectorAll('[aria-hidden="true"]')
    // Logo orb + 3 floating shapes + scroll indicator + arrow SVG = at least 5
    expect(decorativeElements.length).toBeGreaterThanOrEqual(5)
  })

  it('renders with different locale', () => {
    render(<LandingHero {...defaultProps} locale="pt-BR" />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/pt-BR/dashboard')
  })

  it('section has hero gradient background class', () => {
    const { container } = render(<LandingHero {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section?.className).toContain('mesh-gradient-hero')
  })
})
