import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DemoTooltip } from './demo-tooltip'
import { useDemoStore } from '@/stores/demo-store'

vi.mock('motion/react', () => ({
  motion: {
    div: ({
      children,
      ...rest
    }: Record<string, unknown> & { children?: React.ReactNode }) => {
      const {
        initial: _i,
        animate: _a,
        exit: _e,
        transition: _t,
        ...safe
      } = rest
      return <div {...safe}>{children}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}))

describe('DemoTooltip', () => {
  beforeEach(() => {
    useDemoStore.setState({
      isDemoMode: false,
      currentStep: 0,
      dismissed: false,
    })
  })

  it('renders nothing when not in demo mode', () => {
    const { container } = render(<DemoTooltip />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when currentStep is 0', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 0 })
    const { container } = render(<DemoTooltip />)
    expect(container.innerHTML).toBe('')
  })

  it('renders tooltip when isDemoMode=true and currentStep > 0', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 1 })
    render(<DemoTooltip />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('demo.step_1')).toBeInTheDocument()
  })

  it('shows step counter', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 2 })
    render(<DemoTooltip />)
    expect(screen.getByText('2/3')).toBeInTheDocument()
  })

  it('next button calls nextStep', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 1 })
    render(<DemoTooltip />)
    const nextBtn = screen.getByText('demo.next')
    fireEvent.click(nextBtn)
    expect(useDemoStore.getState().currentStep).toBe(2)
  })

  it('skip button calls exitDemo', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 1 })
    render(<DemoTooltip />)
    const skipBtn = screen.getByText('demo.skip')
    fireEvent.click(skipBtn)
    expect(useDemoStore.getState().isDemoMode).toBe(false)
  })

  it('shows complete button on step 3', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 3 })
    render(<DemoTooltip />)
    expect(screen.getByText('demo.complete')).toBeInTheDocument()
  })

  it('complete button exits demo', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 3 })
    render(<DemoTooltip />)
    const completeBtn = screen.getByText('demo.complete')
    fireEvent.click(completeBtn)
    expect(useDemoStore.getState().isDemoMode).toBe(false)
  })
})
