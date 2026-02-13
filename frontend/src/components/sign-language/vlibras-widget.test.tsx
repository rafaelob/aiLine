import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VLibrasWidget } from './vlibras-widget'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

describe('VLibrasWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the container with aria-label', () => {
    render(<VLibrasWidget />)
    const container = screen.getByLabelText('vlibras.aria_label')
    expect(container).toBeInTheDocument()
  })

  it('renders the instruction text', () => {
    render(<VLibrasWidget />)
    expect(
      screen.getByText('vlibras.help_text')
    ).toBeInTheDocument()
  })

  it('renders vw widget HTML via dangerouslySetInnerHTML', () => {
    const { container } = render(<VLibrasWidget />)
    const vwDiv = container.querySelector('[vw="true"]')
    expect(vwDiv).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<VLibrasWidget className="custom-class" />)
    const container = screen.getByLabelText('vlibras.aria_label')
    expect(container).toHaveClass('custom-class')
  })

  it('defaults position to right', () => {
    const { container } = render(<VLibrasWidget />)
    const button = container.querySelector('[vw-access-button]')
    expect(button?.getAttribute('style')).toContain('right: 10px')
  })

  it('uses left position when specified', () => {
    const { container } = render(<VLibrasWidget position="left" />)
    const button = container.querySelector('[vw-access-button]')
    expect(button?.getAttribute('style')).toContain('left: 10px')
  })

  // FINDING-26: aria-hidden + skip-link
  it('has aria-hidden="true" when widget is inactive (before script loads)', () => {
    render(<VLibrasWidget />)
    const container = screen.getByLabelText('vlibras.aria_label')
    expect(container).toHaveAttribute('aria-hidden', 'true')
  })

  it('has tabIndex={-1} when inactive', () => {
    render(<VLibrasWidget />)
    const container = screen.getByLabelText('vlibras.aria_label')
    expect(container).toHaveAttribute('tabindex', '-1')
  })

  it('renders a skip-link before the widget', () => {
    render(<VLibrasWidget />)
    const skipLink = screen.getByText('vlibras.skip_widget')
    expect(skipLink).toBeInTheDocument()
    expect(skipLink.tagName).toBe('A')
    expect(skipLink).toHaveAttribute('href', '#vlibras-after')
  })

  it('renders the skip-link target anchor after the widget', () => {
    const { container } = render(<VLibrasWidget />)
    const target = container.querySelector('#vlibras-after')
    expect(target).toBeInTheDocument()
  })
})
