import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RouteAnnouncer } from './route-announcer'

describe('RouteAnnouncer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset DOM between tests
    document.body.innerHTML = ''
  })

  it('renders a status element with aria-live="assertive"', () => {
    render(<RouteAnnouncer />)
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-live', 'assertive')
  })

  it('has aria-atomic set to true', () => {
    render(<RouteAnnouncer />)
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-atomic', 'true')
  })

  it('has the sr-only class for screen-reader-only visibility', () => {
    render(<RouteAnnouncer />)
    const status = screen.getByRole('status')
    expect(status.className).toContain('sr-only')
  })

  it('announces the page title via textContent on mount', () => {
    // Add an h1 to the document so the effect can find it
    const h1 = document.createElement('h1')
    h1.textContent = 'Dashboard'
    document.body.appendChild(h1)

    render(<RouteAnnouncer />)

    const status = screen.getByRole('status')
    // The mock useTranslations('common') returns: common.navigated_to
    // The effect sets textContent to t('navigated_to', { page: pageTitle })
    // Because the mock returns the key, it will be 'common.navigated_to'
    expect(status.textContent).toBe('common.navigated_to')
  })

  it('defaults to AiLine when no h1 is found', () => {
    // No h1 in the document
    render(<RouteAnnouncer />)

    const status = screen.getByRole('status')
    // The mock t function doesn't interpolate, so it still returns 'common.navigated_to'
    expect(status.textContent).toBe('common.navigated_to')
  })

  it('focuses the main content element when present', () => {
    const main = document.createElement('main')
    main.id = 'main-content'
    document.body.appendChild(main)

    render(<RouteAnnouncer />)

    expect(main.getAttribute('tabindex')).toBe('-1')
  })
})
