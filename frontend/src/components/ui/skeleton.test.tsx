import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton, SkeletonCard, SkeletonCardGrid } from './skeleton'

describe('Skeleton', () => {
  it('renders a single skeleton line by default', () => {
    const { container } = render(<Skeleton />)
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons).toHaveLength(1)
  })

  it('renders multiple skeleton lines', () => {
    const { container } = render(<Skeleton lines={4} />)
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons).toHaveLength(4)
  })

  it('is hidden from screen readers', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstChild as HTMLElement
    expect(el).toHaveAttribute('aria-hidden', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="h-8 w-32" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('h-8')
    expect(el.className).toContain('w-32')
  })
})

describe('SkeletonCard', () => {
  it('renders a card skeleton', () => {
    const { container } = render(<SkeletonCard />)
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })

  it('is hidden from screen readers', () => {
    const { container } = render(<SkeletonCard />)
    const el = container.firstChild as HTMLElement
    expect(el).toHaveAttribute('aria-hidden', 'true')
  })

  it('has animate-pulse class for subtle pulsing', () => {
    const { container } = render(<SkeletonCard />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('animate-pulse')
  })
})

describe('SkeletonCardGrid', () => {
  it('renders 4 cards by default', () => {
    const { container } = render(<SkeletonCardGrid />)
    const cards = container.querySelectorAll('[aria-hidden="true"]')
    // 1 grid container + 4 cards + inner aria-hidden elements
    // Check direct children of the grid
    const grid = container.firstChild as HTMLElement
    expect(grid.children).toHaveLength(4)
  })

  it('renders custom count of cards', () => {
    const { container } = render(<SkeletonCardGrid count={6} />)
    const grid = container.firstChild as HTMLElement
    expect(grid.children).toHaveLength(6)
  })

  it('is hidden from screen readers', () => {
    const { container } = render(<SkeletonCardGrid />)
    const grid = container.firstChild as HTMLElement
    expect(grid).toHaveAttribute('aria-hidden', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonCardGrid className="gap-8" />)
    const grid = container.firstChild as HTMLElement
    expect(grid.className).toContain('gap-8')
  })
})
