import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FeatureShowcase } from './feature-showcase'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    h2: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <h2 {...safe}>{children as React.ReactNode}</h2>
    },
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
  },
}))

describe('FeatureShowcase', () => {
  it('renders the features heading', () => {
    render(<FeatureShowcase />)
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toHaveTextContent('landing.features_title')
  })

  it('renders all 6 feature cards', () => {
    render(<FeatureShowcase />)
    const articles = screen.getAllByRole('article')
    expect(articles.length).toBe(6)
  })

  it('renders feature titles', () => {
    render(<FeatureShowcase />)
    expect(screen.getByText('landing.feature_pipeline')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_accessibility')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_sign')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_curriculum')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_tutor')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_models')).toBeInTheDocument()
  })

  it('renders feature descriptions', () => {
    render(<FeatureShowcase />)
    expect(screen.getByText('landing.feature_pipeline_desc')).toBeInTheDocument()
    expect(screen.getByText('landing.feature_accessibility_desc')).toBeInTheDocument()
  })

  it('renders tech stack badges', () => {
    render(<FeatureShowcase />)
    expect(screen.getByText('Next.js 16')).toBeInTheDocument()
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
    expect(screen.getByText('Pydantic AI')).toBeInTheDocument()
    expect(screen.getByText('LangGraph')).toBeInTheDocument()
    expect(screen.getByText('Claude')).toBeInTheDocument()
    expect(screen.getByText('GPT')).toBeInTheDocument()
    expect(screen.getByText('Gemini')).toBeInTheDocument()
  })

  it('renders the tech title heading', () => {
    render(<FeatureShowcase />)
    expect(screen.getByText('landing.tech_title')).toBeInTheDocument()
  })

  it('renders the built with badge', () => {
    render(<FeatureShowcase />)
    expect(screen.getByText('landing.built_with')).toBeInTheDocument()
  })
})
