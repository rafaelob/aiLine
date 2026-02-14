import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PreferencesPanel } from './preferences-panel'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ref, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, onKeyDown, ...safe } = rest
      return (
        <div ref={ref as React.Ref<HTMLDivElement>} onKeyDown={onKeyDown as React.KeyboardEventHandler} {...safe}>
          {children as React.ReactNode}
        </div>
      )
    },
  },
}))

const mockSetTheme = vi.fn()
const mockSetFontSize = vi.fn()
const mockSetReducedMotion = vi.fn()
const mockToggleFocusMode = vi.fn()
const mockToggleBionicReading = vi.fn()

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: () => ({
    theme: 'standard',
    fontSize: 'medium',
    reducedMotion: false,
    focusMode: false,
    bionicReading: false,
    setTheme: mockSetTheme,
    setFontSize: mockSetFontSize,
    setReducedMotion: mockSetReducedMotion,
    toggleFocusMode: mockToggleFocusMode,
    toggleBionicReading: mockToggleBionicReading,
  }),
}))

describe('PreferencesPanel', () => {
  const user = userEvent.setup()
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders as a dialog with aria-modal', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  it('renders the title from translations', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    expect(screen.getByText('accessibility.title')).toBeInTheDocument()
  })

  it('renders a close button', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const closeButton = screen.getByLabelText('accessibility.close')
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const closeButton = screen.getByLabelText('accessibility.close')
    await user.click(closeButton)
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('renders theme radio options', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const radioGroups = screen.getAllByRole('radiogroup')
    expect(radioGroups.length).toBeGreaterThanOrEqual(1)
  })

  it('renders font size options', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    // Font sizes: small, medium, large, xlarge
    const radios = screen.getAllByRole('radio')
    expect(radios.length).toBeGreaterThanOrEqual(4)
  })

  it('renders motion preference options', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    expect(screen.getByText('accessibility.motion_full')).toBeInTheDocument()
    expect(screen.getByText('accessibility.motion_reduced')).toBeInTheDocument()
  })

  it('calls onClose on Escape key', async () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const dialog = screen.getByRole('dialog')
    dialog.focus()
    await user.keyboard('{Escape}')
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('renders focus mode and bionic reading toggle switches', () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const switches = screen.getAllByRole('switch')
    expect(switches).toHaveLength(2)
    expect(switches[0]).toHaveAttribute('aria-checked', 'false')
    expect(switches[1]).toHaveAttribute('aria-checked', 'false')
  })

  it('calls toggleFocusMode when focus mode switch is clicked', async () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const switches = screen.getAllByRole('switch')
    await user.click(switches[0])
    expect(mockToggleFocusMode).toHaveBeenCalledTimes(1)
  })

  it('calls toggleBionicReading when bionic reading switch is clicked', async () => {
    render(<PreferencesPanel onClose={mockOnClose} />)
    const switches = screen.getAllByRole('switch')
    await user.click(switches[1])
    expect(mockToggleBionicReading).toHaveBeenCalledTimes(1)
  })
})
