import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { HeroSection } from './hero-section'

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
}))

describe('HeroSection', () => {
  it('renders with accessible section and heading', () => {
    render(<HeroSection />)
    const section = screen.getByRole('region', { name: 'landing.hero_title' })
    expect(section).toBeInTheDocument()
  })

  it('renders the main title', () => {
    render(<HeroSection />)
    const title = screen.getByRole('heading', { level: 1 })
    expect(title).toHaveTextContent('landing.hero_title')
  })

  it('renders the subtitle', () => {
    render(<HeroSection />)
    expect(screen.getByText('landing.hero_subtitle')).toBeInTheDocument()
  })

  it('renders all 4 stats badges', () => {
    render(<HeroSection />)
    expect(screen.getByText('9')).toBeInTheDocument()
    // "3" appears twice (Languages and Models)
    expect(screen.getAllByText('3').length).toBe(2)
    expect(screen.getByText('BNCC + US')).toBeInTheDocument()
    expect(screen.getByText('landing.stats_personas')).toBeInTheDocument()
    expect(screen.getByText('landing.stats_languages')).toBeInTheDocument()
    expect(screen.getByText('landing.stats_models')).toBeInTheDocument()
    expect(screen.getByText('landing.stats_standards')).toBeInTheDocument()
  })

  it('renders the Start Demo CTA button', () => {
    render(<HeroSection />)
    const button = screen.getByRole('button', { name: /landing\.start_demo/i })
    expect(button).toBeInTheDocument()
  })

  it('calls onStartDemo when CTA is clicked', () => {
    const onStartDemo = vi.fn()
    render(<HeroSection onStartDemo={onStartDemo} />)
    const button = screen.getByRole('button', { name: /landing\.start_demo/i })

    fireEvent.click(button)

    expect(onStartDemo).toHaveBeenCalledOnce()
  })

  it('renders the hackathon badge', () => {
    render(<HeroSection />)
    expect(screen.getByText('landing.built_with')).toBeInTheDocument()
  })

  it('renders the AiLine brand name', () => {
    render(<HeroSection />)
    expect(screen.getByText('AiLine')).toBeInTheDocument()
  })
})
