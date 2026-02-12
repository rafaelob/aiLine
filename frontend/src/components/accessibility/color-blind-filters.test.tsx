import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { ColorBlindFilters } from './color-blind-filters'

describe('ColorBlindFilters', () => {
  it('renders a hidden SVG element', () => {
    const { container } = render(<ColorBlindFilters />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })

  it('contains protanopia filter', () => {
    const { container } = render(<ColorBlindFilters />)
    const filter = container.querySelector('#cb-protanopia')
    expect(filter).toBeInTheDocument()
    expect(filter?.tagName).toBe('filter')
  })

  it('contains deuteranopia filter', () => {
    const { container } = render(<ColorBlindFilters />)
    const filter = container.querySelector('#cb-deuteranopia')
    expect(filter).toBeInTheDocument()
    expect(filter?.tagName).toBe('filter')
  })

  it('contains tritanopia filter', () => {
    const { container } = render(<ColorBlindFilters />)
    const filter = container.querySelector('#cb-tritanopia')
    expect(filter).toBeInTheDocument()
    expect(filter?.tagName).toBe('filter')
  })

  it('each filter has a feColorMatrix element', () => {
    const { container } = render(<ColorBlindFilters />)
    const matrices = container.querySelectorAll('feColorMatrix')
    expect(matrices).toHaveLength(3)
  })

  it('all feColorMatrix elements use type="matrix"', () => {
    const { container } = render(<ColorBlindFilters />)
    const matrices = container.querySelectorAll('feColorMatrix')
    for (const matrix of matrices) {
      expect(matrix).toHaveAttribute('type', 'matrix')
    }
  })
})
