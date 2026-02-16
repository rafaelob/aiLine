import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AnimatedCounter } from './animated-counter'

vi.mock('motion/react', () => ({
  useMotionValue: () => ({ get: () => 0, set: () => {}, on: () => () => {} }),
  animate: () => ({ stop: () => {} }),
  useInView: () => true,
  useReducedMotion: () => true,
}))

describe('AnimatedCounter', () => {
  it('renders without crashing', () => {
    render(<AnimatedCounter value={10} />)
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('displays value with suffix', () => {
    render(<AnimatedCounter value={9} suffix="+" />)
    expect(screen.getByText('9+')).toBeInTheDocument()
  })

  it('displays value without suffix when not provided', () => {
    render(<AnimatedCounter value={42} />)
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders aria-live region when label is provided and animation completes', async () => {
    const { container } = render(
      <AnimatedCounter value={5} suffix="+" label="Models" />
    )
    // queueMicrotask defers the done state, so wait for it
    await waitFor(() => {
      const srOnly = container.querySelector('.sr-only')
      expect(srOnly).toBeInTheDocument()
      expect(srOnly).toHaveAttribute('aria-live', 'polite')
      expect(srOnly?.textContent).toContain('5')
      expect(srOnly?.textContent).toContain('Models')
    })
  })

  it('does not render aria-live region when label is not provided', async () => {
    const { container } = render(<AnimatedCounter value={5} suffix="+" />)
    // Wait for any microtasks to settle
    await waitFor(() => {
      expect(container.querySelector('.sr-only')).not.toBeInTheDocument()
    })
  })

  it('renders the span element for the counter value', () => {
    const { container } = render(<AnimatedCounter value={100} suffix="%" />)
    const span = container.querySelector('span')
    expect(span).toBeInTheDocument()
    expect(span?.textContent).toBe('100%')
  })

  it('uses default spring config when none provided', () => {
    render(<AnimatedCounter value={7} />)
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('accepts custom spring config', () => {
    const customSpring = { stiffness: 80, damping: 18, mass: 0.6 }
    render(<AnimatedCounter value={3} suffix="+" spring={customSpring} />)
    expect(screen.getByText('3+')).toBeInTheDocument()
  })
})
