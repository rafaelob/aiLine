import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CognitiveLoadMeter, type CognitiveLoadFactors } from './cognitive-load-meter'

const lowFactors: CognitiveLoadFactors = {
  uiDensity: 20,
  readingLevel: 15,
  interactionCount: 2,
}

const mediumFactors: CognitiveLoadFactors = {
  uiDensity: 55,
  readingLevel: 50,
  interactionCount: 5,
}

const highFactors: CognitiveLoadFactors = {
  uiDensity: 85,
  readingLevel: 80,
  interactionCount: 8,
}

describe('CognitiveLoadMeter', () => {
  it('renders title', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('cognitive_load.title')).toBeInTheDocument()
  })

  it('shows low level for low factors', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('cognitive_load.low')).toBeInTheDocument()
  })

  it('shows medium level for medium factors', () => {
    render(<CognitiveLoadMeter factors={mediumFactors} />)
    expect(screen.getByText('cognitive_load.medium')).toBeInTheDocument()
  })

  it('shows high level for high factors', () => {
    render(<CognitiveLoadMeter factors={highFactors} />)
    expect(screen.getByText('cognitive_load.high')).toBeInTheDocument()
  })

  it('renders factor values', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('20')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('renders factor labels', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('cognitive_load.ui_density')).toBeInTheDocument()
    expect(screen.getByText('cognitive_load.reading_level')).toBeInTheDocument()
    expect(screen.getByText('cognitive_load.interaction_count')).toBeInTheDocument()
  })

  it('renders progress bar with correct aria attributes', () => {
    render(<CognitiveLoadMeter factors={mediumFactors} />)
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toHaveAttribute('aria-valuemin', '0')
    expect(progressbar).toHaveAttribute('aria-valuemax', '100')
    expect(progressbar).toHaveAttribute('aria-label', 'cognitive_load.score_label')
  })

  it('shows low suggestion for low factors', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('cognitive_load.suggestion_low')).toBeInTheDocument()
  })

  it('shows medium suggestion for medium factors', () => {
    render(<CognitiveLoadMeter factors={mediumFactors} />)
    expect(screen.getByText('cognitive_load.suggestion_medium')).toBeInTheDocument()
  })

  it('shows high suggestion for high factors', () => {
    render(<CognitiveLoadMeter factors={highFactors} />)
    expect(screen.getByText('cognitive_load.suggestion_high')).toBeInTheDocument()
  })

  it('renders score as number/100', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    // low: 20*0.4 + 15*0.35 + min(100, 20)*0.25 = 8 + 5.25 + 5 = 18.25 -> 18
    expect(screen.getByText('18/100')).toBeInTheDocument()
  })

  it('renders factors heading', () => {
    render(<CognitiveLoadMeter factors={lowFactors} />)
    expect(screen.getByText('cognitive_load.factors')).toBeInTheDocument()
  })
})
