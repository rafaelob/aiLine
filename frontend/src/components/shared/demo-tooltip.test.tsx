import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DemoTooltip } from './demo-tooltip'
import { useDemoStore, TEACHER_STEPS } from '@/stores/demo-store'

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
      activeTrack: null,
      currentStep: 0,
      dismissed: false,
    })
  })

  it('renders nothing when not in demo mode', () => {
    const { container } = render(<DemoTooltip />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when no track is selected', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: null, currentStep: 0 })
    const { container } = render(<DemoTooltip />)
    expect(container.innerHTML).toBe('')
  })

  it('renders tooltip with teacher track', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 0 })
    render(<DemoTooltip />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    // Step title and description should render (i18n keys in test)
    expect(screen.getByText('demo.teacher.step1_title')).toBeInTheDocument()
  })

  it('shows step counter', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 1 })
    render(<DemoTooltip />)
    expect(screen.getByText(`2/${TEACHER_STEPS.length}`)).toBeInTheDocument()
  })

  it('next button calls nextStep', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 0 })
    render(<DemoTooltip />)
    const nextBtn = screen.getByText('demo.next')
    fireEvent.click(nextBtn)
    expect(useDemoStore.getState().currentStep).toBe(1)
  })

  it('skip button calls exitDemo', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 0 })
    render(<DemoTooltip />)
    const skipBtn = screen.getByText('demo.skip')
    fireEvent.click(skipBtn)
    expect(useDemoStore.getState().isDemoMode).toBe(false)
  })

  it('shows complete button on last step', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'teacher',
      currentStep: TEACHER_STEPS.length - 1,
    })
    render(<DemoTooltip />)
    expect(screen.getByText('demo.complete')).toBeInTheDocument()
  })

  it('complete button exits demo on last step', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'teacher',
      currentStep: TEACHER_STEPS.length - 1,
    })
    render(<DemoTooltip />)
    const completeBtn = screen.getByText('demo.complete')
    fireEvent.click(completeBtn)
    expect(useDemoStore.getState().isDemoMode).toBe(false)
  })

  it('shows back button when not on first step', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 2 })
    render(<DemoTooltip />)
    expect(screen.getByText('demo.prev')).toBeInTheDocument()
  })

  it('does not show back button on first step', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 0 })
    render(<DemoTooltip />)
    expect(screen.queryByText('demo.prev')).not.toBeInTheDocument()
  })

  it('renders accessibility track', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'accessibility', currentStep: 0 })
    render(<DemoTooltip />)
    expect(screen.getByText(/demo\.track_a11y/)).toBeInTheDocument()
    expect(screen.getByText('demo.a11y.step1_title')).toBeInTheDocument()
  })

  it('shows track badge for teacher', () => {
    useDemoStore.setState({ isDemoMode: true, activeTrack: 'teacher', currentStep: 0 })
    render(<DemoTooltip />)
    expect(screen.getByText(/demo\.track_teacher/)).toBeInTheDocument()
  })
})
