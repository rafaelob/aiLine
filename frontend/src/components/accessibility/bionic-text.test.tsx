import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BionicText } from './bionic-text'

const mockUseAccessibilityStore = vi.fn()

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector(mockUseAccessibilityStore()),
}))

vi.mock('dompurify', () => ({
  default: { sanitize: (html: string) => html },
}))

describe('BionicText', () => {
  it('renders plain text when bionicReading is false', () => {
    mockUseAccessibilityStore.mockReturnValue({ bionicReading: false })
    render(<BionicText>Hello world</BionicText>)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
    expect(screen.getByText('Hello world').tagName).toBe('P')
  })

  it('renders bionic HTML when bionicReading is true', () => {
    mockUseAccessibilityStore.mockReturnValue({ bionicReading: true })
    const { container } = render(<BionicText>Hello world</BionicText>)
    const boldTags = container.querySelectorAll('b')
    expect(boldTags.length).toBeGreaterThan(0)
  })

  it('respects the "as" prop', () => {
    mockUseAccessibilityStore.mockReturnValue({ bionicReading: false })
    render(<BionicText as="span">Test</BionicText>)
    expect(screen.getByText('Test').tagName).toBe('SPAN')
  })

  it('applies className', () => {
    mockUseAccessibilityStore.mockReturnValue({ bionicReading: false })
    render(<BionicText className="test-class">Text</BionicText>)
    expect(screen.getByText('Text')).toHaveClass('test-class')
  })
})
