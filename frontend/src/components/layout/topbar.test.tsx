import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TopBar } from './topbar'

vi.mock('@/components/accessibility/preferences-panel', () => ({
  PreferencesPanel: ({ open, onClose }: { open: boolean; onClose: () => void }) => (
    open ? (
      <div data-testid="preferences-panel">
        <button onClick={onClose}>Close Panel</button>
      </div>
    ) : null
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
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders as a banner landmark', async () => {
    await act(async () => { render(<TopBar />) })
    const banner = screen.getByRole('banner')
    expect(banner).toBeInTheDocument()
  })

  it('renders locale switcher as a radiogroup', async () => {
    await act(async () => { render(<TopBar />) })
    const radiogroup = screen.getByRole('radiogroup', { name: 'topbar.locale_label' })
    expect(radiogroup).toBeInTheDocument()
  })

  it('renders all locale radio buttons', async () => {
    await act(async () => { render(<TopBar />) })
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(3)
    expect(screen.getByText('EN')).toBeInTheDocument()
    expect(screen.getByText('PT')).toBeInTheDocument()
    expect(screen.getByText('ES')).toBeInTheDocument()
  })

  it('has full locale names as aria-labels', async () => {
    await act(async () => { render(<TopBar />) })
    expect(screen.getByLabelText('English')).toBeInTheDocument()
    expect(screen.getByLabelText('Português (BR)')).toBeInTheDocument()
    expect(screen.getByLabelText('Español')).toBeInTheDocument()
  })

  it('renders accessibility toggle button', async () => {
    await act(async () => { render(<TopBar />) })
    const button = screen.getByLabelText('topbar.accessibility')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-expanded', 'false')
  })

  it('opens preferences panel on accessibility button click', async () => {
    await act(async () => { render(<TopBar />) })
    const button = screen.getByLabelText('topbar.accessibility')
    await user.click(button)

    expect(screen.getByTestId('preferences-panel')).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })

  it('closes preferences panel when close is triggered', async () => {
    await act(async () => { render(<TopBar />) })
    const button = screen.getByLabelText('topbar.accessibility')
    await user.click(button)

    const closeButton = screen.getByText('Close Panel')
    await user.click(closeButton)

    expect(screen.queryByTestId('preferences-panel')).not.toBeInTheDocument()
  })

  it('displays accessibility text on wider screens', async () => {
    await act(async () => { render(<TopBar />) })
    expect(screen.getByText('topbar.accessibility')).toBeInTheDocument()
  })

  it('renders system status button', async () => {
    await act(async () => { render(<TopBar />) })
    const statusBtn = screen.getByLabelText('topbar.system_status')
    expect(statusBtn).toBeInTheDocument()
  })

  it('shows status dropdown on click', async () => {
    await act(async () => { render(<TopBar />) })
    const statusBtn = screen.getByLabelText('topbar.system_status')
    await user.click(statusBtn)
    expect(screen.getByRole('dialog', { name: 'topbar.system_status' })).toBeInTheDocument()
  })
})
