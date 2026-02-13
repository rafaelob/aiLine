import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { InteractiveCard } from './interactive-card'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, whileHover: _h, whileTap: _t, initial: _i, animate: _a, transition: _tr, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
}))

describe('InteractiveCard', () => {
  it('renders children', () => {
    render(<InteractiveCard>Card Content</InteractiveCard>)
    expect(screen.getByText('Card Content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<InteractiveCard className="p-4">Content</InteractiveCard>)
    const card = screen.getByText('Content').closest('div')
    expect(card).toHaveClass('p-4')
  })

  it('applies theme-aware border and background classes', () => {
    render(<InteractiveCard>Content</InteractiveCard>)
    const card = screen.getByText('Content').closest('div')
    expect(card?.className).toContain('bg-[var(--color-surface)]')
    expect(card?.className).toContain('border-[var(--color-border)]')
  })

  it('applies cursor-pointer class', () => {
    render(<InteractiveCard>Content</InteractiveCard>)
    const card = screen.getByText('Content').closest('div')
    expect(card).toHaveClass('cursor-pointer')
  })
})
