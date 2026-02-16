import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DashboardPage from './page'

vi.mock('@/components/dashboard/dashboard-content', () => ({
  DashboardContent: () => (
    <div data-testid="dashboard-content">Dashboard Content</div>
  ),
}))

describe('DashboardPage', () => {
  it('renders the DashboardContent component', () => {
    render(<DashboardPage />)
    expect(screen.getByTestId('dashboard-content')).toBeInTheDocument()
  })

  it('wraps content in a max-width container', () => {
    const { container } = render(<DashboardPage />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('max-w-5xl')
  })

  it('applies mx-auto for centering', () => {
    const { container } = render(<DashboardPage />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('mx-auto')
  })

  it('renders a single root element', () => {
    const { container } = render(<DashboardPage />)
    expect(container.children).toHaveLength(1)
  })

  it('renders DashboardContent as the only child', () => {
    const { container } = render(<DashboardPage />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.children).toHaveLength(1)
    expect(wrapper.querySelector('[data-testid="dashboard-content"]')).toBeInTheDocument()
  })
})
