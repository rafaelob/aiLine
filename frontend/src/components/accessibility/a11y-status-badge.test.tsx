import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { A11yStatusBadge } from './a11y-status-badge'
import { useAccessibilityStore } from '@/stores/accessibility-store'

describe('A11yStatusBadge', () => {
  beforeEach(() => {
    useAccessibilityStore.setState({
      theme: 'standard',
      fontSize: 'medium',
      reducedMotion: false,
      focusMode: false,
      bionicReading: false,
    })
  })

  it('renders badge with default persona icon and name', () => {
    render(<A11yStatusBadge />)
    const badge = screen.getByRole('button', { name: /accessibility.status_badge_label/i })
    expect(badge).toBeInTheDocument()
  })

  it('shows persona name in the badge', () => {
    render(<A11yStatusBadge />)
    expect(screen.getByText('accessibility.themes.standard')).toBeInTheDocument()
  })

  it('does not show feature count when no features are active', () => {
    render(<A11yStatusBadge />)
    expect(screen.queryByText(/features_active/)).not.toBeInTheDocument()
  })

  it('shows feature count when features are active', () => {
    useAccessibilityStore.setState({
      theme: 'tea',
      reducedMotion: true,
      focusMode: true,
    })
    render(<A11yStatusBadge />)
    // theme !== standard + reducedMotion + focusMode = 3
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('expands on click to show feature details', () => {
    render(<A11yStatusBadge />)
    const badge = screen.getByRole('button', { name: /accessibility.status_badge_label/i })
    fireEvent.click(badge)
    expect(screen.getByText('accessibility.font_size')).toBeInTheDocument()
    expect(screen.getByText('accessibility.motion')).toBeInTheDocument()
    expect(screen.getByText('accessibility.focusMode')).toBeInTheDocument()
    expect(screen.getByText('accessibility.bionicReading')).toBeInTheDocument()
  })

  it('sets aria-expanded correctly', () => {
    render(<A11yStatusBadge />)
    const badge = screen.getByRole('button', { name: /accessibility.status_badge_label/i })
    expect(badge).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(badge)
    expect(badge).toHaveAttribute('aria-expanded', 'true')
  })

  it('shows active persona label when expanded', () => {
    useAccessibilityStore.setState({ theme: 'dyslexia' })
    render(<A11yStatusBadge />)
    fireEvent.click(screen.getByRole('button', { name: /accessibility.status_badge_label/i }))
    expect(screen.getByText('accessibility.active_persona')).toBeInTheDocument()
  })

  it('shows feature values correctly for non-default state', () => {
    useAccessibilityStore.setState({
      fontSize: 'large',
      reducedMotion: true,
      focusMode: true,
      bionicReading: true,
    })
    render(<A11yStatusBadge />)
    fireEvent.click(screen.getByRole('button', { name: /accessibility.status_badge_label/i }))
    expect(screen.getByText('accessibility.font_size_large')).toBeInTheDocument()
    expect(screen.getByText('accessibility.motion_reduced')).toBeInTheDocument()
    // Focus and bionic show "On"
    const onLabels = screen.getAllByText('accessibility.badge_on')
    expect(onLabels).toHaveLength(2)
  })

  it('closes on Escape key', () => {
    render(<A11yStatusBadge />)
    const badge = screen.getByRole('button', { name: /accessibility.status_badge_label/i })
    fireEvent.click(badge)
    expect(badge).toHaveAttribute('aria-expanded', 'true')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(badge).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes on outside click', () => {
    render(<A11yStatusBadge />)
    const badge = screen.getByRole('button', { name: /accessibility.status_badge_label/i })
    fireEvent.click(badge)
    expect(badge).toHaveAttribute('aria-expanded', 'true')
    fireEvent.mouseDown(document.body)
    expect(badge).toHaveAttribute('aria-expanded', 'false')
  })

  it('has status role on expanded panel', () => {
    render(<A11yStatusBadge />)
    fireEvent.click(screen.getByRole('button', { name: /accessibility.status_badge_label/i }))
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
