import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { InstallPrompt } from './install-prompt'

/** Helper to fire a mock beforeinstallprompt event. */
function fireInstallPromptEvent() {
  const event = new Event('beforeinstallprompt', { cancelable: true })
  Object.defineProperty(event, 'prompt', {
    value: vi.fn().mockResolvedValue(undefined),
  })
  window.dispatchEvent(event)
  return event
}

describe('InstallPrompt', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders nothing when no beforeinstallprompt event fires', () => {
    const { container } = render(<InstallPrompt />)
    expect(container.innerHTML).toBe('')
  })

  it('shows the install banner when beforeinstallprompt fires', async () => {
    render(<InstallPrompt />)

    // useEffect has run after render; fire the event
    await act(async () => {
      fireInstallPromptEvent()
    })

    expect(screen.getByText('pwa.install_title')).toBeDefined()
  })

  it('dismisses the banner and stores dismissal time', async () => {
    render(<InstallPrompt />)

    await act(async () => {
      fireInstallPromptEvent()
    })

    fireEvent.click(screen.getByLabelText('pwa.dismiss_label'))

    // Banner should be gone
    expect(screen.queryByText('pwa.install_title')).toBeNull()
    // Dismissal should be stored
    expect(localStorage.getItem('ailine-pwa-dismissed')).toBeTruthy()
  })

  it('does not show banner if dismissed within 30 days', async () => {
    // Set dismissal to 10 days ago
    const tenDaysAgo = Date.now() - 10 * 24 * 60 * 60 * 1000
    localStorage.setItem('ailine-pwa-dismissed', String(tenDaysAgo))

    render(<InstallPrompt />)

    await act(async () => {
      fireInstallPromptEvent()
    })

    // Should not show because user dismissed recently
    expect(screen.queryByText('pwa.install_title')).toBeNull()
  })

  it('has proper aria-label on the install container', async () => {
    render(<InstallPrompt />)

    await act(async () => {
      fireInstallPromptEvent()
    })

    // The container div has role="alertdialog" and aria-label
    const containers = screen.getAllByLabelText('pwa.install_label')
    expect(containers.length).toBeGreaterThanOrEqual(1)
    // One of them should be the alertdialog container
    const alertDialogContainer = containers.find(
      (el) => el.getAttribute('role') === 'alertdialog'
    )
    expect(alertDialogContainer).toBeDefined()
  })
})
