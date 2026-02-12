import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton, SkeletonCard } from './skeleton'

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
})
