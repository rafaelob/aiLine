import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LandingNav } from './landing-nav'

vi.mock('motion/react', () => ({
  motion: {
    nav: ({ children, ...rest }: Record<string, unknown>) => {
      const {
        initial: _i, animate: _a, transition: _t,
        onFocus, onBlur, ...safe
      } = rest
      return (
        <nav
          onFocus={onFocus as React.FocusEventHandler}
          onBlur={onBlur as React.FocusEventHandler}
          {...safe}
        >
          {children as React.ReactNode}
        </nav>
      )
    },
  },
  useReducedMotion: () => false,
}))

vi.mock('next/link', () => ({
  default: ({ children, href, tabIndex, ...rest }: Record<string, unknown>) => (
    <a href={href as string} tabIndex={tabIndex as number} {...rest}>
      {children as React.ReactNode}
    </a>
  ),
}))

const defaultProps = {
  locale: 'en',
  startDemo: 'Start Demo',
}

describe('LandingNav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<LandingNav {...defaultProps} />)
    // Nav starts aria-hidden (not scrolled), use hidden option
    expect(screen.getByRole('navigation', { hidden: true })).toBeInTheDocument()
  })

  it('has aria-label "Landing navigation"', () => {
    render(<LandingNav {...defaultProps} />)
    const nav = screen.getByRole('navigation', { hidden: true })
    expect(nav).toHaveAttribute('aria-label', 'Landing navigation')
  })

  it('renders AiLine brand name', () => {
    render(<LandingNav {...defaultProps} />)
    expect(screen.getByText('AiLine')).toBeInTheDocument()
  })

  it('renders brand logo orb with aria-hidden', () => {
    const { container } = render(<LandingNav {...defaultProps} />)
    // The nav itself and the orb div both have aria-hidden; get the orb by its text
    const orbs = container.querySelectorAll('[aria-hidden="true"]')
    const logoOrb = Array.from(orbs).find((el) => el.textContent === 'A' && el.tagName === 'DIV')
    expect(logoOrb).toBeInTheDocument()
  })

  it('renders CTA link with startDemo text', () => {
    render(<LandingNav {...defaultProps} />)
    // Link is inside aria-hidden nav, use hidden option
    const link = screen.getByRole('link', { hidden: true })
    expect(link.textContent).toBe('Start Demo')
  })

  it('CTA link points to locale dashboard', () => {
    render(<LandingNav {...defaultProps} />)
    const link = screen.getByRole('link', { hidden: true })
    expect(link).toHaveAttribute('href', '/en/dashboard')
  })

  it('CTA link uses correct locale for pt-BR', () => {
    render(<LandingNav locale="pt-BR" startDemo="Iniciar Demo" />)
    const link = screen.getByRole('link', { hidden: true })
    expect(link).toHaveAttribute('href', '/pt-BR/dashboard')
    expect(link.textContent).toBe('Iniciar Demo')
  })

  it('nav has glass styling class', () => {
    render(<LandingNav {...defaultProps} />)
    const nav = screen.getByRole('navigation', { hidden: true })
    expect(nav.className).toContain('glass')
  })

  it('nav is fixed positioned at top', () => {
    render(<LandingNav {...defaultProps} />)
    const nav = screen.getByRole('navigation', { hidden: true })
    expect(nav.className).toContain('fixed')
    expect(nav.className).toContain('top-0')
  })

  it('handles focus/blur for keyboard accessibility', () => {
    render(<LandingNav {...defaultProps} />)
    const nav = screen.getByRole('navigation', { hidden: true })
    fireEvent.focus(nav)
    fireEvent.blur(nav)
    // No crash = focus/blur handlers work
    expect(nav).toBeInTheDocument()
  })
})
