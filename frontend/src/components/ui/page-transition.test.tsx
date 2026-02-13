import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageTransition } from './page-transition'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

describe('PageTransition', () => {
  it('renders children', () => {
    render(
      <PageTransition>
        <p>Hello</p>
      </PageTransition>
    )
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders multiple children', () => {
    render(
      <PageTransition>
        <p>First</p>
        <p>Second</p>
      </PageTransition>
    )
    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
  })

  it('wraps children in a div container', () => {
    const { container } = render(
      <PageTransition>
        <span>Content</span>
      </PageTransition>
    )
    expect(container.firstChild?.nodeName).toBe('DIV')
  })

  it('preserves children structure', () => {
    render(
      <PageTransition>
        <div data-testid="inner">
          <p>Nested</p>
        </div>
      </PageTransition>
    )
    const inner = screen.getByTestId('inner')
    expect(inner).toBeInTheDocument()
    expect(inner.querySelector('p')).toHaveTextContent('Nested')
  })
})
