import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MotorStickyToolbar } from './motor-sticky-toolbar'
import { useAccessibilityStore } from '@/stores/accessibility-store'

describe('MotorStickyToolbar', () => {
  beforeEach(() => {
    useAccessibilityStore.setState({
      theme: 'standard',
      fontSize: 'medium',
      reducedMotion: false,
      focusMode: false,
      bionicReading: false,
      lowDistraction: false,
    })
  })

  it('does not render when theme is not motor', () => {
    const { container } = render(<MotorStickyToolbar />)
    expect(container.firstChild).toBeNull()
  })

  it('renders toolbar when theme is motor', () => {
    useAccessibilityStore.setState({ theme: 'motor' })
    render(<MotorStickyToolbar />)
    const toolbar = screen.getByRole('toolbar')
    expect(toolbar).toBeInTheDocument()
  })

  it('has accessible label', () => {
    useAccessibilityStore.setState({ theme: 'motor' })
    render(<MotorStickyToolbar />)
    expect(screen.getByRole('toolbar')).toHaveAttribute(
      'aria-label',
      'motor_toolbar.label'
    )
  })

  it('renders 4 action buttons', () => {
    useAccessibilityStore.setState({ theme: 'motor' })
    render(<MotorStickyToolbar />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(4)
  })

  it('scroll-to-top button scrolls main content', () => {
    useAccessibilityStore.setState({ theme: 'motor' })

    const mockScroll = vi.fn()
    const mockFocus = vi.fn()
    const mockMain = {
      scrollTo: mockScroll,
      focus: mockFocus,
    }
    vi.spyOn(document, 'getElementById').mockReturnValue(mockMain as unknown as HTMLElement)

    render(<MotorStickyToolbar />)
    const scrollBtn = screen.getByLabelText('motor_toolbar.scroll_top')
    fireEvent.click(scrollBtn)

    expect(mockScroll).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
    expect(mockFocus).toHaveBeenCalledWith({ preventScroll: true })
  })

  it('font increase button increases font size', () => {
    useAccessibilityStore.setState({ theme: 'motor', fontSize: 'medium' })
    render(<MotorStickyToolbar />)

    const increaseBtn = screen.getByLabelText('motor_toolbar.font_increase')
    fireEvent.click(increaseBtn)

    expect(useAccessibilityStore.getState().fontSize).toBe('large')
  })

  it('font decrease button decreases font size', () => {
    useAccessibilityStore.setState({ theme: 'motor', fontSize: 'large' })
    render(<MotorStickyToolbar />)

    const decreaseBtn = screen.getByLabelText('motor_toolbar.font_decrease')
    fireEvent.click(decreaseBtn)

    expect(useAccessibilityStore.getState().fontSize).toBe('medium')
  })

  it('font decrease is disabled at smallest size', () => {
    useAccessibilityStore.setState({ theme: 'motor', fontSize: 'small' })
    render(<MotorStickyToolbar />)

    const decreaseBtn = screen.getByLabelText('motor_toolbar.font_decrease')
    expect(decreaseBtn).toBeDisabled()
  })

  it('font increase is disabled at largest size', () => {
    useAccessibilityStore.setState({ theme: 'motor', fontSize: 'xlarge' })
    render(<MotorStickyToolbar />)

    const increaseBtn = screen.getByLabelText('motor_toolbar.font_increase')
    expect(increaseBtn).toBeDisabled()
  })

  it('focus mode toggle works', () => {
    useAccessibilityStore.setState({ theme: 'motor', focusMode: false })
    render(<MotorStickyToolbar />)

    const focusBtn = screen.getByLabelText('motor_toolbar.focus_on')
    expect(focusBtn).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(focusBtn)
    expect(useAccessibilityStore.getState().focusMode).toBe(true)
  })

  it('focus button shows active state when focus mode is on', () => {
    useAccessibilityStore.setState({ theme: 'motor', focusMode: true })
    render(<MotorStickyToolbar />)

    const focusBtn = screen.getByLabelText('motor_toolbar.focus_off')
    expect(focusBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('disappears when theme changes away from motor', () => {
    useAccessibilityStore.setState({ theme: 'motor' })
    const { rerender } = render(<MotorStickyToolbar />)
    expect(screen.getByRole('toolbar')).toBeInTheDocument()

    useAccessibilityStore.setState({ theme: 'standard' })
    rerender(<MotorStickyToolbar />)
    expect(screen.queryByRole('toolbar')).not.toBeInTheDocument()
  })
})
