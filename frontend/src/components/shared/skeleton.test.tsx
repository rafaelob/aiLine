import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton, SkeletonCard } from './skeleton'

describe('Skeleton', () => {
  it('renders with role="status"', () => {
    render(<Skeleton />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has an accessible loading label', () => {
    render(<Skeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading...')
  })

  it('renders text variant by default', () => {
    render(<Skeleton />)
    const el = screen.getByRole('status')
    // text variant applies h-4 and rounded-sm
    expect(el.className).toContain('h-4')
  })

  it('renders circular variant', () => {
    render(<Skeleton variant="circular" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('rounded-full')
  })

  it('renders rectangular variant', () => {
    render(<Skeleton variant="rectangular" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('rounded-[var(--radius-md)]')
  })

  it('applies the animate-pulse class', () => {
    render(<Skeleton />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('animate-pulse')
  })

  it('applies width style when provided as string', () => {
    render(<Skeleton width="200px" />)
    const el = screen.getByRole('status')
    expect(el).toHaveStyle({ width: '200px' })
  })

  it('applies height style when provided as string', () => {
    render(<Skeleton height="48px" />)
    const el = screen.getByRole('status')
    expect(el).toHaveStyle({ height: '48px' })
  })

  it('applies width and height as numbers', () => {
    render(<Skeleton width={120} height={32} />)
    const el = screen.getByRole('status')
    expect(el).toHaveStyle({ width: '120px', height: '32px' })
  })

  it('applies custom className', () => {
    render(<Skeleton className="w-full" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('w-full')
  })
})

describe('SkeletonCard', () => {
  it('renders multiple skeleton elements inside', () => {
    render(<SkeletonCard />)
    const skeletons = screen.getAllByRole('status')
    // The card contains 4 Skeleton elements: 2 text + 2 rectangular
    expect(skeletons.length).toBe(4)
  })

  it('applies custom className to the card wrapper', () => {
    const { container } = render(<SkeletonCard className="my-card-class" />)
    const wrapper = container.firstElementChild
    expect(wrapper?.className).toContain('my-card-class')
  })

  it('renders with card-like styling', () => {
    const { container } = render(<SkeletonCard />)
    const wrapper = container.firstElementChild
    expect(wrapper?.className).toContain('rounded-[var(--radius-lg)]')
    expect(wrapper?.className).toContain('border')
  })
})
