import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ObservabilityPage from './page'

vi.mock('@/components/observability/observability-dashboard', () => ({
  default: () => <div data-testid="dashboard-content">Dashboard</div>,
}))

describe('ObservabilityPage', () => {
  it('renders the page title', () => {
    render(<ObservabilityPage />)
    expect(screen.getByText('observability.title')).toBeInTheDocument()
  })

  it('renders the page description', () => {
    render(<ObservabilityPage />)
    expect(screen.getByText('observability.description')).toBeInTheDocument()
  })

  it('renders the dashboard content component', async () => {
    render(<ObservabilityPage />)
    expect(await screen.findByTestId('dashboard-content')).toBeInTheDocument()
  })
})
