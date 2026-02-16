import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingFooter } from './landing-footer'

const defaultProps = {
  builtWith: 'Built with Claude Opus 4.6',
  openSource: 'Open Source — MIT License',
  createdWith: 'Created with Claude Code',
  hackathon: 'Hackathon "Built with Opus 4.6" — February 2026',
}

describe('LandingFooter', () => {
  it('renders without crashing', () => {
    render(<LandingFooter {...defaultProps} />)
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('renders the builtWith badge text', () => {
    render(<LandingFooter {...defaultProps} />)
    expect(screen.getByText('Built with Claude Opus 4.6')).toBeInTheDocument()
  })

  it('renders copyright with current year', () => {
    render(<LandingFooter {...defaultProps} />)
    const year = new Date().getFullYear().toString()
    const copyright = screen.getByText(new RegExp(`\\u00a9.*${year}.*AiLine`))
    expect(copyright).toBeInTheDocument()
  })

  it('renders copyright with AiLine name', () => {
    render(<LandingFooter {...defaultProps} />)
    const copyright = screen.getByText(/AiLine/)
    expect(copyright).toBeInTheDocument()
  })

  it('footer is a semantic footer element', () => {
    render(<LandingFooter {...defaultProps} />)
    const footer = screen.getByRole('contentinfo')
    expect(footer.tagName).toBe('FOOTER')
  })

  it('badge icon is hidden from assistive tech', () => {
    const { container } = render(<LandingFooter {...defaultProps} />)
    const hiddenEl = container.querySelector('[aria-hidden="true"]')
    expect(hiddenEl).toBeInTheDocument()
  })

  it('footer has top border for visual separation', () => {
    render(<LandingFooter {...defaultProps} />)
    const footer = screen.getByRole('contentinfo')
    expect(footer.className).toContain('border-t')
  })

  it('renders open source badge', () => {
    render(<LandingFooter {...defaultProps} />)
    expect(screen.getByText('Open Source — MIT License')).toBeInTheDocument()
  })

  it('renders created with badge', () => {
    render(<LandingFooter {...defaultProps} />)
    expect(screen.getByText('Created with Claude Code')).toBeInTheDocument()
  })

  it('renders hackathon line', () => {
    render(<LandingFooter {...defaultProps} />)
    expect(screen.getByText(/Hackathon/)).toBeInTheDocument()
  })

  it('renders with different builtWith text', () => {
    render(<LandingFooter {...{ ...defaultProps, builtWith: 'Powered by AI' }} />)
    expect(screen.getByText('Powered by AI')).toBeInTheDocument()
  })

  it('renders GitHub icon', () => {
    const { container } = render(<LandingFooter {...defaultProps} />)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThanOrEqual(2) // layers icon + github icon
  })
})
