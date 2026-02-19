import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingFeatures } from './landing-features'

vi.mock('motion/react', () => ({
  motion: {
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, whileInView: _w, viewport: _v, ...safe } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, whileInView: _w, viewport: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  useReducedMotion: () => false,
}))

const sampleFeatures = [
  { title: 'AI Pipeline', desc: 'Multi-agent lesson plan generation', icon: 'pipeline' as const },
  { title: 'Accessibility', desc: '9 disability personas', icon: 'a11y' as const },
  { title: 'Tutor', desc: 'Conversational AI tutor', icon: 'tutor' as const },
  { title: 'Multi-Model', desc: '5+ LLM providers', icon: 'models' as const },
  { title: 'Sign Language', desc: 'LIBRAS recognition', icon: 'sign' as const },
  { title: 'Curriculum', desc: 'BNCC alignment', icon: 'curriculum' as const },
]

describe('LandingFeatures', () => {
  it('renders without crashing', () => {
    render(<LandingFeatures title="Features" features={sampleFeatures} />)
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument()
  })

  it('renders the section title', () => {
    render(<LandingFeatures title="Our Features" features={sampleFeatures} />)
    expect(screen.getByText('Our Features')).toBeInTheDocument()
  })

  it('renders all 6 feature cards', () => {
    render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const articles = screen.getAllByRole('article')
    expect(articles).toHaveLength(6)
  })

  it('renders feature titles', () => {
    render(<LandingFeatures title="Features" features={sampleFeatures} />)
    expect(screen.getByText('AI Pipeline')).toBeInTheDocument()
    expect(screen.getByText('Accessibility')).toBeInTheDocument()
    expect(screen.getByText('Tutor')).toBeInTheDocument()
    expect(screen.getByText('Multi-Model')).toBeInTheDocument()
    expect(screen.getByText('Sign Language')).toBeInTheDocument()
    expect(screen.getByText('Curriculum')).toBeInTheDocument()
  })

  it('renders feature descriptions', () => {
    render(<LandingFeatures title="Features" features={sampleFeatures} />)
    expect(screen.getByText('Multi-agent lesson plan generation')).toBeInTheDocument()
    expect(screen.getByText('9 disability personas')).toBeInTheDocument()
    expect(screen.getByText('Conversational AI tutor')).toBeInTheDocument()
    expect(screen.getByText('5+ LLM providers')).toBeInTheDocument()
    expect(screen.getByText('LIBRAS recognition')).toBeInTheDocument()
    expect(screen.getByText('BNCC alignment')).toBeInTheDocument()
  })

  it('section has aria-labelledby pointing to features-heading', () => {
    const { container } = render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const section = container.querySelector('section')
    expect(section).toHaveAttribute('aria-labelledby', 'features-heading')
  })

  it('heading has id="features-heading"', () => {
    render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toHaveAttribute('id', 'features-heading')
  })

  it('renders feature icons with aria-hidden', () => {
    const { container } = render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const svgs = container.querySelectorAll('svg[aria-hidden="true"]')
    // Each feature card has an icon SVG
    expect(svgs.length).toBeGreaterThanOrEqual(6)
  })

  it('uses responsive grid layout', () => {
    const { container } = render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const grid = container.querySelector('.grid')
    expect(grid).toBeInTheDocument()
    expect(grid?.className).toContain('sm:grid-cols-2')
    expect(grid?.className).toContain('lg:grid-cols-3')
  })

  it('renders with empty features array', () => {
    render(<LandingFeatures title="Features" features={[]} />)
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.queryAllByRole('article')).toHaveLength(0)
  })

  it('feature cards have glass styling', () => {
    const { container } = render(<LandingFeatures title="Features" features={sampleFeatures} />)
    const firstArticle = container.querySelector('article')
    expect(firstArticle?.className).toContain('glass')
    expect(firstArticle?.className).toContain('card-hover')
  })
})
