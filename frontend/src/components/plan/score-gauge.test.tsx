import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ScoreGauge } from './score-gauge'

// Mock motion/react to render static elements
vi.mock('motion/react', () => ({
  motion: {
    circle: ({ initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <circle {...rest} />
    },
    span: ({ children, initial: _i, animate: _a, transition: _t, style, ...rest }: Record<string, unknown>) => {
      return <span style={style as React.CSSProperties} {...rest}>{children as React.ReactNode}</span>
    },
  },
  useSpring: (initial: number) => ({
    set: vi.fn(),
    get: () => initial,
    on: (_event: string, cb: (v: number) => void) => {
      cb(initial)
      return () => {}
    },
  }),
  useTransform: (_spring: unknown, transform: (v: number) => number) => ({
    get: () => transform(0),
    on: (_event: string, cb: (v: number) => void) => {
      cb(transform(0))
      return () => {}
    },
  }),
}))

describe('ScoreGauge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with the correct ARIA attributes', () => {
    render(<ScoreGauge score={75} />)

    const meter = screen.getByRole('meter')
    expect(meter).toBeInTheDocument()
    expect(meter).toHaveAttribute('aria-valuenow', '75')
    expect(meter).toHaveAttribute('aria-valuemin', '0')
    expect(meter).toHaveAttribute('aria-valuemax', '100')
    expect(meter).toHaveAttribute('aria-label', 'Quality score: 75 out of 100')
  })

  it('clamps score to 0-100 range', () => {
    const { rerender } = render(<ScoreGauge score={150} />)
    let meter = screen.getByRole('meter')
    expect(meter).toHaveAttribute('aria-valuenow', '100')

    rerender(<ScoreGauge score={-20} />)
    meter = screen.getByRole('meter')
    expect(meter).toHaveAttribute('aria-valuenow', '0')
  })

  it('renders SVG with the specified size', () => {
    render(<ScoreGauge score={50} size={200} />)

    const svg = document.querySelector('svg')
    expect(svg).toHaveAttribute('width', '200')
    expect(svg).toHaveAttribute('height', '200')
  })

  it('renders the "/ 100" label', () => {
    render(<ScoreGauge score={85} />)
    expect(screen.getByText('/ 100')).toBeInTheDocument()
  })

  it('uses default size of 160', () => {
    render(<ScoreGauge score={50} />)

    const svg = document.querySelector('svg')
    expect(svg).toHaveAttribute('width', '160')
    expect(svg).toHaveAttribute('height', '160')
  })

  it('renders two circles (background track + progress arc)', () => {
    render(<ScoreGauge score={50} />)

    const circles = document.querySelectorAll('circle')
    expect(circles.length).toBe(2)
  })
})
