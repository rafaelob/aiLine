import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingFooter } from './landing-footer'

describe('LandingFooter', () => {
  it('renders without crashing', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('renders the builtWith badge text', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    expect(screen.getByText('Built with Claude Opus 4.6')).toBeInTheDocument()
  })

  it('renders copyright with current year', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    const year = new Date().getFullYear().toString()
    const copyright = screen.getByText(new RegExp(year))
    expect(copyright).toBeInTheDocument()
  })

  it('renders copyright with AiLine name', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    const copyright = screen.getByText(/AiLine/)
    expect(copyright).toBeInTheDocument()
  })

  it('footer is a semantic footer element', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    const footer = screen.getByRole('contentinfo')
    expect(footer.tagName).toBe('FOOTER')
  })

  it('badge icon is hidden from assistive tech', () => {
    const { container } = render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    const hiddenEl = container.querySelector('[aria-hidden="true"]')
    expect(hiddenEl).toBeInTheDocument()
  })

  it('footer has top border for visual separation', () => {
    render(<LandingFooter builtWith="Built with Claude Opus 4.6" />)
    const footer = screen.getByRole('contentinfo')
    expect(footer.className).toContain('border-t')
  })

  it('renders with different builtWith text', () => {
    render(<LandingFooter builtWith="Powered by AI" />)
    expect(screen.getByText('Powered by AI')).toBeInTheDocument()
  })
})
