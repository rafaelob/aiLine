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
})
