import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RoleIcon } from './role-icon'

describe('RoleIcon', () => {
  it('renders an SVG with the given path', () => {
    const { container } = render(<RoleIcon path="M12 0L24 24H0z" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    const path = container.querySelector('path')
    expect(path).toHaveAttribute('d', 'M12 0L24 24H0z')
  })

  it('is aria-hidden', () => {
    const { container } = render(<RoleIcon path="M0 0" />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<RoleIcon path="M0 0" className="custom-class" />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('custom-class')
  })

  it('has correct viewBox and dimensions', () => {
    const { container } = render(<RoleIcon path="M0 0" />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('viewBox', '0 0 24 24')
    expect(svg).toHaveAttribute('width', '28')
    expect(svg).toHaveAttribute('height', '28')
  })
})
