import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingPage } from './landing-page'

vi.mock('./landing-nav', () => ({
  LandingNav: ({ locale, startDemo }: { locale: string; startDemo: string }) => (
    <nav data-testid="landing-nav" data-locale={locale}>{startDemo}</nav>
  ),
}))

vi.mock('./landing-hero', () => ({
  LandingHero: ({ title, subtitle, cta }: { title: string; subtitle: string; cta: string }) => (
    <section data-testid="landing-hero">
      <h1>{title}</h1>
      <p>{subtitle}</p>
      <span>{cta}</span>
    </section>
  ),
}))

vi.mock('./landing-features', () => ({
  LandingFeatures: ({ title, features }: { title: string; features: { title: string }[] }) => (
    <section data-testid="landing-features">
      <h2>{title}</h2>
      {features.map((f) => (
        <div key={f.title}>{f.title}</div>
      ))}
    </section>
  ),
}))

vi.mock('./landing-stats', () => ({
  LandingStats: ({ sectionLabel }: { sectionLabel: string }) => (
    <section data-testid="landing-stats">{sectionLabel}</section>
  ),
}))

vi.mock('./landing-footer', () => ({
  LandingFooter: ({ builtWith }: { builtWith: string }) => (
    <footer data-testid="landing-footer">{builtWith}</footer>
  ),
}))

const defaultProps = {
  locale: 'en',
  heroTitle: 'Hero Title',
  heroSubtitle: 'Hero Subtitle',
  startDemo: 'Start Demo',
  statsPersonas: 'Personas',
  statsLanguages: 'Languages',
  statsModels: 'Models',
  statsStandards: 'Standards',
  statsLabel: 'Stats',
  featuresTitle: 'Features',
  featurePipeline: 'Pipeline',
  featurePipelineDesc: 'Pipeline desc',
  featureAccessibility: 'Accessibility',
  featureAccessibilityDesc: 'A11y desc',
  featureTutor: 'Tutor',
  featureTutorDesc: 'Tutor desc',
  featureModels: 'Models Feature',
  featureModelsDesc: 'Models desc',
  featureSign: 'Sign Language',
  featureSignDesc: 'Sign desc',
  featureCurriculum: 'Curriculum',
  featureCurriculumDesc: 'Curriculum desc',
  builtWith: 'Built with Claude',
}

describe('LandingPage', () => {
  it('renders without crashing', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-nav')).toBeInTheDocument()
    expect(screen.getByTestId('landing-hero')).toBeInTheDocument()
    expect(screen.getByTestId('landing-features')).toBeInTheDocument()
    expect(screen.getByTestId('landing-stats')).toBeInTheDocument()
    expect(screen.getByTestId('landing-footer')).toBeInTheDocument()
  })

  it('renders a main content area', () => {
    render(<LandingPage {...defaultProps} />)
    const main = document.getElementById('main-content')
    expect(main).toBeInTheDocument()
    expect(main?.tagName).toBe('MAIN')
  })

  it('passes locale to LandingNav', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-nav')).toHaveAttribute('data-locale', 'en')
  })

  it('passes hero props correctly', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByText('Hero Title')).toBeInTheDocument()
    expect(screen.getByText('Hero Subtitle')).toBeInTheDocument()
  })

  it('passes features title and feature items', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Pipeline')).toBeInTheDocument()
    expect(screen.getByText('Accessibility')).toBeInTheDocument()
    expect(screen.getByText('Tutor')).toBeInTheDocument()
    expect(screen.getByText('Models Feature')).toBeInTheDocument()
    expect(screen.getByText('Sign Language')).toBeInTheDocument()
    expect(screen.getByText('Curriculum')).toBeInTheDocument()
  })

  it('passes stats label', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByText('Stats')).toBeInTheDocument()
  })

  it('passes builtWith to footer', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByText('Built with Claude')).toBeInTheDocument()
  })

  it('passes startDemo to nav CTA', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-nav').textContent).toBe('Start Demo')
  })

  it('renders full-screen layout with min-h-screen', () => {
    const { container } = render(<LandingPage {...defaultProps} />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper.className).toContain('min-h-screen')
    expect(wrapper.className).toContain('flex')
    expect(wrapper.className).toContain('flex-col')
  })
})
