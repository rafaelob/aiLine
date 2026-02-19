import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingPage, type LandingPageProps } from './landing-page'

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

vi.mock('./landing-how-it-works', () => ({
  LandingHowItWorks: ({ title }: { title: string }) => (
    <section data-testid="landing-how-it-works">{title}</section>
  ),
}))

vi.mock('./landing-demo-login', () => ({
  LandingDemoLogin: ({ title }: { title: string }) => (
    <section data-testid="landing-demo-login">{title}</section>
  ),
}))

vi.mock('./landing-footer', () => ({
  LandingFooter: ({ builtWith }: { builtWith: string }) => (
    <footer data-testid="landing-footer">{builtWith}</footer>
  ),
}))

const defaultProps: LandingPageProps = {
  locale: 'en',
  startDemo: 'Try the Demo',
  hero: {
    title: 'AiLine',
    subtitle: 'Hero Subtitle',
    fullName: 'Adaptive Inclusive Learning',
    badgeOpenSource: 'Open Source',
    badgeBuiltWith: 'Built with Claude Code',
  },
  stats: {
    personas: 'Personas',
    languages: 'Languages',
    models: 'Models',
    standards: 'Standards',
    label: 'Stats',
  },
  features: {
    title: 'Features',
    items: [
      { title: 'Pipeline', desc: 'Pipeline desc', icon: 'pipeline' },
      { title: 'Accessibility', desc: 'A11y desc', icon: 'a11y' },
      { title: 'Tutor', desc: 'Tutor desc', icon: 'tutor' },
      { title: 'Models Feature', desc: 'Models desc', icon: 'models' },
      { title: 'Sign Language', desc: 'Sign desc', icon: 'sign' },
      { title: 'Curriculum', desc: 'Curriculum desc', icon: 'curriculum' },
    ],
  },
  howItWorks: {
    title: 'How It Works',
    steps: [
      { title: 'Step 1', description: 'Desc 1' },
      { title: 'Step 2', description: 'Desc 2' },
      { title: 'Step 3', description: 'Desc 3' },
      { title: 'Step 4', description: 'Desc 4' },
    ],
  },
  demo: {
    title: 'Try the Demo',
    subtitle: 'Choose a profile',
    enterAs: 'Enter',
    teacherLabel: 'Teacher',
    studentLabel: 'Student',
    parentLabel: 'Parent',
    profiles: {
      teacher: { name: 'Sarah', detail: '5th Grade', description: 'Desc' },
      students: {
        alex: { name: 'Alex', condition: 'ASD', description: 'Desc' },
        maya: { name: 'Maya', condition: 'ADHD', description: 'Desc' },
        lucas: { name: 'Lucas', condition: 'Dyslexia', description: 'Desc' },
        sofia: { name: 'Sofia', condition: 'Hearing', description: 'Desc' },
      },
      parent: { name: 'David', description: 'Desc' },
    },
  },
  footer: {
    builtWith: 'Built with Claude',
    openSource: 'Open Source — MIT',
    createdWith: 'Created with Claude Code',
    hackathon: 'Hackathon Feb 2026',
  },
}

describe('LandingPage', () => {
  it('renders without crashing', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-nav')).toBeInTheDocument()
    expect(screen.getByTestId('landing-hero')).toBeInTheDocument()
    expect(screen.getByTestId('landing-features')).toBeInTheDocument()
    expect(screen.getByTestId('landing-stats')).toBeInTheDocument()
    expect(screen.getByTestId('landing-how-it-works')).toBeInTheDocument()
    expect(screen.getByTestId('landing-demo-login')).toBeInTheDocument()
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
    expect(screen.getByText('AiLine')).toBeInTheDocument()
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

  it('renders how-it-works section', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-how-it-works')).toHaveTextContent('How It Works')
  })

  it('renders demo login section', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-demo-login')).toHaveTextContent('Try the Demo')
  })

  it('passes startDemo to nav CTA', () => {
    render(<LandingPage {...defaultProps} />)
    expect(screen.getByTestId('landing-nav').textContent).toBe('Try the Demo')
  })

  it('renders full-screen layout with min-h-screen', () => {
    const { container } = render(<LandingPage {...defaultProps} />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper.className).toContain('min-h-screen')
    expect(wrapper.className).toContain('flex')
    expect(wrapper.className).toContain('flex-col')
  })
})
