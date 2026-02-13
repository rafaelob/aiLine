import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import NotFoundPage from './not-found'

describe('NotFoundPage', () => {
  it('renders the not found title', () => {
    render(<NotFoundPage />)
    expect(screen.getByText('common.not_found_title')).toBeInTheDocument()
  })

  it('renders the not found description', () => {
    render(<NotFoundPage />)
    expect(screen.getByText('common.not_found_description')).toBeInTheDocument()
  })

  it('renders the 404 indicator', () => {
    render(<NotFoundPage />)
    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('renders go home link pointing to root', () => {
    render(<NotFoundPage />)
    const link = screen.getByText('common.go_home')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })

  it('404 indicator is aria-hidden', () => {
    const { container } = render(<NotFoundPage />)
    const indicator = container.querySelector('[aria-hidden="true"]')
    expect(indicator).toBeInTheDocument()
  })

  it('has a heading element', () => {
    render(<NotFoundPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading.textContent).toBe('common.not_found_title')
  })

  it('go home link has appropriate styling classes', () => {
    render(<NotFoundPage />)
    const link = screen.getByText('common.go_home')
    expect(link.className).toContain('rounded')
  })
})
