import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Loading from './loading'

describe('PlansLoading', () => {
  it('renders loading skeleton with status role', () => {
    render(<Loading />)
    const statusElements = screen.getAllByRole('status')
    expect(statusElements.length).toBeGreaterThanOrEqual(1)
  })

  it('has accessible label', () => {
    render(<Loading />)
    expect(screen.getByLabelText('Loading plans')).toBeInTheDocument()
  })

  it('contains sr-only loading text', () => {
    render(<Loading />)
    expect(screen.getByText('Loading plans...')).toBeInTheDocument()
  })
})
