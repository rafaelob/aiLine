import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { EmptyState } from './empty-state'

// Mock motion/react to render static elements
vi.mock('motion/react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('motion/react')>()
  return {
    ...actual,
    motion: {
      div: ({ children, ...rest }: Record<string, unknown>) => {
        const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
        return React.createElement('div', safe, children as React.ReactNode)
      },
    },
    useReducedMotion: () => false,
  }
})

describe('EmptyState', () => {
  it('renders the title', () => {
    render(<EmptyState title="No items found" />)
    expect(screen.getByText('No items found')).toBeInTheDocument()
  })

  it('renders the title as an h3 heading', () => {
    render(<EmptyState title="Empty list" />)
    const heading = screen.getByRole('heading', { level: 3 })
    expect(heading).toHaveTextContent('Empty list')
  })

  it('renders description when provided', () => {
    render(<EmptyState title="No items" description="Try creating a new item" />)
    expect(screen.getByText('Try creating a new item')).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    const { container } = render(<EmptyState title="No items" />)
    const paragraphs = container.querySelectorAll('p')
    expect(paragraphs.length).toBe(0)
  })

  it('renders action when provided', () => {
    render(
      <EmptyState
        title="No items"
        action={<button>Create item</button>}
      />
    )
    expect(screen.getByRole('button', { name: 'Create item' })).toBeInTheDocument()
  })

  it('does not render action wrapper when action is not provided', () => {
    const { container } = render(<EmptyState title="No items" />)
    // Only the icon wrapper (if icon provided) and the h3 should be direct children
    const outerDiv = container.firstElementChild!
    // h3 is always present; no extra wrapping divs for action
    const childDivs = outerDiv.querySelectorAll(':scope > div')
    expect(childDivs.length).toBe(0)
  })

  it('renders icon when provided', () => {
    render(
      <EmptyState
        title="No items"
        icon={<span data-testid="custom-icon">icon</span>}
      />
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })

  it('marks the icon container as aria-hidden', () => {
    render(
      <EmptyState
        title="No items"
        icon={<span data-testid="custom-icon">icon</span>}
      />
    )
    const iconContainer = screen.getByTestId('custom-icon').parentElement
    expect(iconContainer).toHaveAttribute('aria-hidden', 'true')
  })

  it('does not render icon container when icon is not provided', () => {
    const { container } = render(<EmptyState title="No items" />)
    const ariaHiddenDivs = container.querySelectorAll('[aria-hidden="true"]')
    expect(ariaHiddenDivs.length).toBe(0)
  })

  it('applies custom className', () => {
    const { container } = render(
      <EmptyState title="No items" className="my-custom-class" />
    )
    const outerDiv = container.firstElementChild
    expect(outerDiv?.className).toContain('my-custom-class')
  })

  it('renders all optional props together', () => {
    render(
      <EmptyState
        title="Nothing here"
        description="Start by adding something"
        icon={<span data-testid="icon">*</span>}
        action={<button>Add new</button>}
        className="extra"
      />
    )

    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    expect(screen.getByText('Start by adding something')).toBeInTheDocument()
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add new' })).toBeInTheDocument()
  })
})
