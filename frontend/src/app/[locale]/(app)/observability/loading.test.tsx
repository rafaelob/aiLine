import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Loading from './loading'

describe('ObservabilityLoading', () => {
  it('renders loading skeleton with status role', () => {
    render(<Loading />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has accessible label', () => {
    render(<Loading />)
    expect(screen.getByLabelText('Loading observability')).toBeInTheDocument()
  })

  it('contains sr-only loading text', () => {
    render(<Loading />)
    expect(screen.getByText('Loading observability dashboard...')).toBeInTheDocument()
  })
})
