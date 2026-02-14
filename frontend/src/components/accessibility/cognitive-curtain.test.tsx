import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { CognitiveCurtain } from './cognitive-curtain'

const mockUseAccessibilityStore = vi.fn()

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector(mockUseAccessibilityStore()),
}))

describe('CognitiveCurtain', () => {
  it('renders nothing when focusMode is false', () => {
    mockUseAccessibilityStore.mockReturnValue({ focusMode: false })
    const { container } = render(<CognitiveCurtain />)
    expect(container.innerHTML).toBe('')
  })

  it('renders a style element when focusMode is true', () => {
    mockUseAccessibilityStore.mockReturnValue({ focusMode: true })
    const { container } = render(<CognitiveCurtain />)
    const style = container.querySelector('style')
    expect(style).not.toBeNull()
    expect(style?.textContent).toContain('.cognitive-curtain-active')
    expect(style?.textContent).toContain('opacity: 0.15')
    expect(style?.textContent).toContain('prefers-reduced-motion')
  })
})
