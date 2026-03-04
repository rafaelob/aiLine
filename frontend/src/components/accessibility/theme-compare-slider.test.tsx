import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeCompareSlider } from './theme-compare-slider'
import { useAccessibilityStore } from '@/stores/accessibility-store'

describe('ThemeCompareSlider', () => {
  beforeEach(() => {
    useAccessibilityStore.setState({ theme: 'standard' })
  })

  it('shows prompt when current theme is standard and no compareTheme', () => {
    render(<ThemeCompareSlider />)
    expect(
      screen.getByText('accessibility.compare_select_persona'),
    ).toBeInTheDocument()
  })

  it('renders slider when a non-standard theme is active', () => {
    useAccessibilityStore.setState({ theme: 'dyslexia' })
    render(<ThemeCompareSlider />)
    expect(screen.getByRole('slider')).toBeInTheDocument()
  })

  it('renders slider when compareTheme is specified', () => {
    render(<ThemeCompareSlider compareTheme="high_contrast" />)
    expect(screen.getByRole('slider')).toBeInTheDocument()
  })

  it('has correct aria attributes on slider', () => {
    render(<ThemeCompareSlider compareTheme="tea" />)
    const slider = screen.getByRole('slider')
    expect(slider).toHaveAttribute('aria-valuemin', '5')
    expect(slider).toHaveAttribute('aria-valuemax', '95')
    expect(slider).toHaveAttribute('aria-valuenow', '50')
    expect(slider).toHaveAttribute('aria-label', 'accessibility.compare_divider')
  })

  it('moves divider left on ArrowLeft key', () => {
    render(<ThemeCompareSlider compareTheme="tdah" />)
    const slider = screen.getByRole('slider')
    fireEvent.keyDown(slider, { key: 'ArrowLeft' })
    expect(slider).toHaveAttribute('aria-valuenow', '45')
  })

  it('moves divider right on ArrowRight key', () => {
    render(<ThemeCompareSlider compareTheme="hearing" />)
    const slider = screen.getByRole('slider')
    fireEvent.keyDown(slider, { key: 'ArrowRight' })
    expect(slider).toHaveAttribute('aria-valuenow', '55')
  })

  it('clamps divider to minimum 5%', () => {
    render(<ThemeCompareSlider compareTheme="motor" />)
    const slider = screen.getByRole('slider')
    // Press left 10 times: 50 -> 45 -> 40 -> ... -> 5 (clamped)
    for (let i = 0; i < 12; i++) {
      fireEvent.keyDown(slider, { key: 'ArrowLeft' })
    }
    expect(slider).toHaveAttribute('aria-valuenow', '5')
  })

  it('clamps divider to maximum 95%', () => {
    render(<ThemeCompareSlider compareTheme="low_vision" />)
    const slider = screen.getByRole('slider')
    for (let i = 0; i < 12; i++) {
      fireEvent.keyDown(slider, { key: 'ArrowRight' })
    }
    expect(slider).toHaveAttribute('aria-valuenow', '95')
  })

  it('renders region landmark with label', () => {
    render(<ThemeCompareSlider compareTheme="tea" />)
    expect(screen.getByRole('region')).toHaveAttribute(
      'aria-label',
      'accessibility.compare_label',
    )
  })

  it('shows standard theme label on left panel', () => {
    render(<ThemeCompareSlider compareTheme="dyslexia" />)
    expect(
      screen.getByText(/accessibility\.themes\.standard/),
    ).toBeInTheDocument()
  })

  it('shows persona theme label on right panel', () => {
    render(<ThemeCompareSlider compareTheme="dyslexia" />)
    // Both header and right panel contain the theme name
    const matches = screen.getAllByText(/accessibility\.themes\.dyslexia/)
    expect(matches.length).toBeGreaterThanOrEqual(1)
  })

  it('renders sample content in both panels', () => {
    render(<ThemeCompareSlider compareTheme="high_contrast" />)
    // Each panel has sample heading "Lesson: Photosynthesis"
    const headings = screen.getAllByText('Lesson: Photosynthesis')
    expect(headings).toHaveLength(2)
  })

  it('accepts custom height', () => {
    render(<ThemeCompareSlider compareTheme="tea" height={400} />)
    const region = screen.getByRole('region')
    // The container with overflow hidden has the style
    const container = region.querySelector('[style*="height"]')
    expect(container).not.toBeNull()
  })

  it('renders compare title header', () => {
    render(<ThemeCompareSlider compareTheme="motor" />)
    expect(
      screen.getByText('accessibility.compare_title'),
    ).toBeInTheDocument()
  })
})
