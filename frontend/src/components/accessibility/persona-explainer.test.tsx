import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PersonaExplainer } from './persona-explainer'
import { useAccessibilityStore } from '@/stores/accessibility-store'

describe('PersonaExplainer', () => {
  beforeEach(() => {
    useAccessibilityStore.setState({ theme: 'standard' })
  })

  it('renders nothing when standard persona is active', () => {
    const { container } = render(<PersonaExplainer />)
    expect(container.innerHTML).toBe('')
  })

  it('renders explainer banner when non-standard persona is active', () => {
    useAccessibilityStore.setState({ theme: 'tea' })
    render(<PersonaExplainer />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows persona name and hint text', () => {
    useAccessibilityStore.setState({ theme: 'dyslexia' })
    render(<PersonaExplainer />)
    expect(screen.getByText('accessibility.themes.dyslexia')).toBeInTheDocument()
    expect(screen.getByText('accessibility.theme_hints.dyslexia')).toBeInTheDocument()
  })

  it('shows persona icon', () => {
    useAccessibilityStore.setState({ theme: 'tdah' })
    render(<PersonaExplainer />)
    // TDAH icon is ⚡
    expect(screen.getByText('\u26A1')).toBeInTheDocument()
  })

  it('shows active persona badge', () => {
    useAccessibilityStore.setState({ theme: 'motor' })
    render(<PersonaExplainer />)
    expect(screen.getByText('accessibility.active_persona')).toBeInTheDocument()
  })

  it('maps high_contrast to hyphenated theme key', () => {
    useAccessibilityStore.setState({ theme: 'high_contrast' })
    render(<PersonaExplainer />)
    expect(screen.getByText('accessibility.themes.high-contrast')).toBeInTheDocument()
  })

  it('maps low_vision to hyphenated theme key', () => {
    useAccessibilityStore.setState({ theme: 'low_vision' })
    render(<PersonaExplainer />)
    expect(screen.getByText('accessibility.themes.low-vision')).toBeInTheDocument()
  })

  it('has aria-live polite for screen reader announcements', () => {
    useAccessibilityStore.setState({ theme: 'hearing' })
    render(<PersonaExplainer />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
  })
})
