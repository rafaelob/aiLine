import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import HomePage from './page'
import type { LandingPageProps } from '@/components/landing/landing-page'

vi.mock('@/components/landing/landing-page', () => ({
  LandingPage: (props: LandingPageProps) => (
    <div data-testid="landing-page">
      <span>{props.hero.title}</span>
      <span>{props.hero.subtitle}</span>
    </div>
  ),
}))

describe('HomePage (Landing)', () => {
  it('renders the LandingPage component', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByTestId('landing-page')).toBeInTheDocument()
  })

  it('passes translated hero title via grouped props', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByText('landing.hero_title')).toBeInTheDocument()
  })

  it('passes translated hero subtitle via grouped props', async () => {
    const page = await HomePage({ params: Promise.resolve({ locale: 'en' }) })
    render(page)
    expect(screen.getByText('landing.hero_subtitle')).toBeInTheDocument()
  })
})
