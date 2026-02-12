import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { A11yHydrator } from './a11y-hydrator'

const mockHydrate = vi.fn()

vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (state: { hydrate: () => void }) => unknown) =>
    selector({ hydrate: mockHydrate }),
}))

describe('A11yHydrator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing (returns null)', () => {
    const { container } = render(<A11yHydrator />)
    expect(container.innerHTML).toBe('')
  })

  it('calls hydrate on mount', () => {
    render(<A11yHydrator />)
    expect(mockHydrate).toHaveBeenCalledTimes(1)
  })
})
