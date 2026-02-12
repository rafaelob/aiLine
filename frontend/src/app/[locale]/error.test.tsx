import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorPage from './error'

describe('ErrorPage', () => {
  const mockError = Object.assign(new Error('Test error'), { digest: 'abc123' })
  const mockReset = vi.fn()

  beforeEach(() => {
    mockReset.mockClear()
  })

  it('renders error title and description', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByText('common.error_title')).toBeInTheDocument()
    expect(screen.getByText('common.error_description')).toBeInTheDocument()
  })

  it('renders error digest when provided', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByText('abc123')).toBeInTheDocument()
  })

  it('hides digest when not provided', () => {
    const errorNoDig = new Error('No digest') as Error & { digest?: string }
    render(<ErrorPage error={errorNoDig} reset={mockReset} />)
    expect(screen.queryByText('abc123')).not.toBeInTheDocument()
  })

  it('calls reset when retry button is clicked', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    fireEvent.click(screen.getByText('common.retry'))
    expect(mockReset).toHaveBeenCalledTimes(1)
  })

  it('renders go home link pointing to root', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    const link = screen.getByText('common.go_home')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })

  it('renders the error icon', () => {
    const { container } = render(<ErrorPage error={mockError} reset={mockReset} />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('logs error to console', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(spy).toHaveBeenCalledWith('[ErrorBoundary]', mockError)
    spy.mockRestore()
  })
})
