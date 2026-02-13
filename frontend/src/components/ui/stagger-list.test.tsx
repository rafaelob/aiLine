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

  it('renders a single item', () => {
    render(
      <StaggerList>
        <StaggerItem>
          <span>Solo</span>
        </StaggerItem>
      </StaggerList>
    )
    expect(screen.getByText('Solo')).toBeInTheDocument()
  })

  it('StaggerItem applies custom className', () => {
    const { container } = render(
      <StaggerList>
        <StaggerItem className="my-class">
          <span>Styled</span>
        </StaggerItem>
      </StaggerList>
    )
    // The StaggerItem div should have the class
    const itemDiv = container.querySelector('.my-class')
    expect(itemDiv).toBeInTheDocument()
  })

  it('renders nested content within StaggerItem', () => {
    render(
      <StaggerList>
        <StaggerItem>
          <div data-testid="nested">
            <p>Deep content</p>
          </div>
        </StaggerItem>
      </StaggerList>
    )
    expect(screen.getByTestId('nested')).toBeInTheDocument()
    expect(screen.getByText('Deep content')).toBeInTheDocument()
  })

  it('renders multiple items preserving order', () => {
    const { container } = render(
      <StaggerList>
        <StaggerItem><span>A</span></StaggerItem>
        <StaggerItem><span>B</span></StaggerItem>
        <StaggerItem><span>C</span></StaggerItem>
      </StaggerList>
    )
    const spans = container.querySelectorAll('span')
    expect(spans[0].textContent).toBe('A')
    expect(spans[1].textContent).toBe('B')
    expect(spans[2].textContent).toBe('C')
  })
})
