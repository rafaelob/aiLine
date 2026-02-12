import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TopBar } from './topbar'

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

vi.mock('@/components/accessibility/preferences-panel', () => ({
  PreferencesPanel: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="preferences-panel">
      <button onClick={onClose}>Close Panel</button>
    </div>
  ),
}))

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: () => ({
    theme: 'standard',
    fontSize: 'medium',
    reducedMotion: false,
    setTheme: vi.fn(),
    setFontSize: vi.fn(),
    setReducedMotion: vi.fn(),
  }),
}))

describe('TopBar', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders as a banner landmark', () => {
    render(<TopBar />)
    const banner = screen.getByRole('banner')
    expect(banner).toBeInTheDocument()
  })

  it('renders locale selector', () => {
    render(<TopBar />)
    const select = screen.getByLabelText('topbar.locale_label')
    expect(select).toBeInTheDocument()
  })

  it('renders all locale options', () => {
    render(<TopBar />)
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('Portugues (BR)')).toBeInTheDocument()
    expect(screen.getByText('Espanol')).toBeInTheDocument()
  })

  it('renders accessibility toggle button', () => {
    render(<TopBar />)
    const button = screen.getByLabelText('topbar.accessibility')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-expanded', 'false')
  })

  it('opens preferences panel on accessibility button click', async () => {
    render(<TopBar />)
    const button = screen.getByLabelText('topbar.accessibility')
    await user.click(button)

    expect(screen.getByTestId('preferences-panel')).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })

  it('closes preferences panel when close is triggered', async () => {
    render(<TopBar />)
    const button = screen.getByLabelText('topbar.accessibility')
    await user.click(button)

    const closeButton = screen.getByText('Close Panel')
    await user.click(closeButton)

    expect(screen.queryByTestId('preferences-panel')).not.toBeInTheDocument()
  })

  it('displays accessibility text on wider screens', () => {
    render(<TopBar />)
    expect(screen.getByText('topbar.accessibility')).toBeInTheDocument()
  })
})
