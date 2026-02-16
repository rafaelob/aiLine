import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DashboardPage from './page'

vi.mock('@/components/dashboard/dashboard-content', () => ({
  DashboardContent: () => (
    <div data-testid="dashboard-content">Dashboard Content</div>
  ),
}))

vi.mock('@/components/ui/page-transition', () => ({
  PageTransition: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="page-transition">{children}</div>
  ),
}))

describe('DashboardPage', () => {
  it('renders the DashboardContent component', () => {
    render(<DashboardPage />)
    expect(screen.getByTestId('dashboard-content')).toBeInTheDocument()
  })

  it('wraps content in a max-width container', () => {
    const { container } = render(<DashboardPage />)
    const inner = container.querySelector('.max-w-5xl')
    expect(inner).toBeInTheDocument()
  })

  it('applies mx-auto for centering', () => {
    const { container } = render(<DashboardPage />)
    const inner = container.querySelector('.mx-auto')
    expect(inner).toBeInTheDocument()
  })

  it('renders a single root element', () => {
    const { container } = render(<DashboardPage />)
    expect(container.children).toHaveLength(1)
  })

  it('renders DashboardContent inside the container', () => {
    const { container } = render(<DashboardPage />)
    const inner = container.querySelector('.max-w-5xl')
    expect(inner).toBeInTheDocument()
    expect(inner?.querySelector('[data-testid="dashboard-content"]')).toBeInTheDocument()
  })
})
