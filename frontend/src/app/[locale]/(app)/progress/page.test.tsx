import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProgressPage from './page'

vi.mock('@/components/progress/progress-dashboard', () => ({
  ProgressDashboard: () => <div data-testid="progress-dashboard">Dashboard</div>,
}))

describe('ProgressPage', () => {
  it('renders heading', async () => {
    const Component = await ProgressPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByText('progress.title')).toBeInTheDocument()
  })

  it('renders ProgressDashboard', async () => {
    const Component = await ProgressPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByTestId('progress-dashboard')).toBeInTheDocument()
  })
})
