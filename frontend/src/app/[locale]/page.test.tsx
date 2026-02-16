import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import HomePage from './page'

vi.mock('@/components/landing/landing-page', () => ({
  LandingPage: (props: Record<string, string>) => (
    <div data-testid="landing-page">
      <span>{props.heroTitle}</span>
      <span>{props.heroSubtitle}</span>
    </div>
  ),
}))

describe('HomePage (Landing)', () => {
  it('renders the LandingPage component', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByTestId('landing-page')).toBeInTheDocument()
  })

  it('passes translated hero title', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByText('landing.hero_title')).toBeInTheDocument()
  })

  it('passes translated hero subtitle', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByText('landing.hero_subtitle')).toBeInTheDocument()
  })
})
