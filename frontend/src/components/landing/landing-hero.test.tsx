import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

const mockSetTheme = vi.fn()
vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ setTheme: mockSetTheme, theme: 'standard' }),
}))

const defaultProps = {
  locale: 'en',
  title: 'AI for Education',
  subtitle: 'Inclusive learning for everyone',
  cta: 'Start Demo',
  fullName: 'Adaptive Inclusive Learning',
  badgeOpenSource: 'Open Source',
  badgeBuiltWith: 'Built with Opus 4.6',
}

describe('LandingHero', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    document.body.removeAttribute('data-theme')
  })

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

  it('CTA link points to demo login section', () => {
    render(<LandingHero {...defaultProps} />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '#demo-login-heading')
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
    // Logo orb + 3 floating shapes + persona dots + scroll indicator + arrow SVG + badge icons
    expect(decorativeElements.length).toBeGreaterThanOrEqual(5)
  })

  it('renders with different locale without breaking CTA', () => {
    render(<LandingHero {...defaultProps} locale="pt-BR" />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '#demo-login-heading')
  })

  it('section has hero gradient background class', () => {
    const { container } = render(<LandingHero {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section?.className).toContain('mesh-gradient-hero')
  })

  // --- Branding badges ---

  it('renders branding badges', () => {
    render(<LandingHero {...defaultProps} />)
    expect(screen.getByText('Open Source')).toBeInTheDocument()
    expect(screen.getByText('Built with Opus 4.6')).toBeInTheDocument()
  })

  // --- Persona preview toggle tests ---

  it('renders persona preview radiogroup', () => {
    render(<LandingHero {...defaultProps} />)
    expect(screen.getByRole('radiogroup')).toBeInTheDocument()
  })

  it('renders 5 persona preview buttons', () => {
    render(<LandingHero {...defaultProps} />)
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(5)
  })

  it('Default persona is checked initially', () => {
    render(<LandingHero {...defaultProps} />)
    const defaultRadio = screen.getByRole('radio', { name: /default/i })
    expect(defaultRadio).toHaveAttribute('aria-checked', 'true')
  })

  it('clicking a persona button calls setTheme and updates data-theme', async () => {
    render(<LandingHero {...defaultProps} />)
    const adhdBtn = screen.getByRole('radio', { name: /adhd/i })
    await user.click(adhdBtn)

    expect(mockSetTheme).toHaveBeenCalledWith('tdah')
    expect(document.body.getAttribute('data-theme')).toBe('tdah')
  })

  it('clicking a persona button updates aria-checked state', async () => {
    render(<LandingHero {...defaultProps} />)
    const teaBtn = screen.getByRole('radio', { name: /asd/i })
    await user.click(teaBtn)

    expect(teaBtn).toHaveAttribute('aria-checked', 'true')
    const defaultBtn = screen.getByRole('radio', { name: /default/i })
    expect(defaultBtn).toHaveAttribute('aria-checked', 'false')
  })

  it('persona buttons have aria-labels', () => {
    render(<LandingHero {...defaultProps} />)
    const radios = screen.getAllByRole('radio')
    for (const radio of radios) {
      expect(radio).toHaveAttribute('aria-label')
    }
  })
})
