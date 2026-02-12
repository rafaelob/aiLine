import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MobileNav } from './mobile-nav'

describe('MobileNav', () => {
  it('renders as a navigation landmark', () => {
    render(<MobileNav />)
    const nav = screen.getByRole('navigation', { name: /Mobile navigation/i })
    expect(nav).toBeInTheDocument()
  })

  it('renders 5 navigation items', () => {
    render(<MobileNav />)
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(5)
  })

  it('renders all nav labels', () => {
    render(<MobileNav />)
    expect(screen.getByText('nav.dashboard')).toBeInTheDocument()
    expect(screen.getByText('nav.plans')).toBeInTheDocument()
    expect(screen.getByText('nav.materials')).toBeInTheDocument()
    expect(screen.getByText('nav.tutors')).toBeInTheDocument()
    expect(screen.getByText('nav.settings')).toBeInTheDocument()
  })

  it('marks dashboard as active on root path', () => {
    render(<MobileNav />)
    const links = screen.getAllByRole('link')
    // First link is dashboard, should be active
    expect(links[0]).toHaveAttribute('aria-current', 'page')
  })
})
