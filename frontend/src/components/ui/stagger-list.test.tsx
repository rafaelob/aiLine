import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StaggerList, StaggerItem } from './stagger-list'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

describe('StaggerList', () => {
  it('renders children', () => {
    render(
      <StaggerList>
        <StaggerItem>
          <span>Item 1</span>
        </StaggerItem>
        <StaggerItem>
          <span>Item 2</span>
        </StaggerItem>
      </StaggerList>
    )
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <StaggerList className="grid gap-4">
        <StaggerItem>
          <span>Test</span>
        </StaggerItem>
      </StaggerList>
    )
    const outer = container.firstChild as HTMLElement
    expect(outer.className).toContain('grid')
  })
})
