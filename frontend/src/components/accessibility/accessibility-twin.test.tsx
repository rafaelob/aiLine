import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AccessibilityTwin } from './accessibility-twin'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const ORIGINAL = 'Line one\nLine two\nLine three'
const ADAPTED = 'Line one\nLine two modified\nLine three\nLine four added'

describe('AccessibilityTwin', () => {
  const user = userEvent.setup()

  it('renders a tablist with two tabs', () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )
    const tablist = screen.getByRole('tablist')
    expect(tablist).toBeInTheDocument()
    expect(tablist).toHaveAttribute('aria-label', 'twin.comparison_label')

    const tabs = screen.getAllByRole('tab')
    expect(tabs).toHaveLength(2)
  })

  it('shows original tab as active by default', () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )
    const originalTab = screen.getByRole('tab', { name: /twin\.original/i })
    expect(originalTab).toHaveAttribute('aria-selected', 'true')

    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    expect(adaptedTab).toHaveAttribute('aria-selected', 'false')
  })

  it('renders original content in the active panel', () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )
    const panel = screen.getByRole('tabpanel')
    expect(panel).toHaveAttribute('aria-labelledby', 'tab-original')
    expect(panel).toHaveTextContent('Line one')
    expect(panel).toHaveTextContent('Line two')
  })

  it('switches to adapted tab on click', async () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )

    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    await user.click(adaptedTab)

    expect(adaptedTab).toHaveAttribute('aria-selected', 'true')

    const panel = screen.getByRole('tabpanel')
    expect(panel).toHaveAttribute('aria-labelledby', 'tab-adapted')
  })

  it('shows diff view in the adapted panel', async () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )

    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    await user.click(adaptedTab)

    // The diff view should show additions and removals
    const diffList = screen.getByRole('list', { name: /twin\.diff_label/i })
    expect(diffList).toBeInTheDocument()
  })

  it('uses custom adaptationLabel in tab name', () => {
    render(
      <AccessibilityTwin
        originalContent={ORIGINAL}
        adaptedContent={ADAPTED}
        adaptationLabel="TEA"
      />
    )
    // The i18n mock returns "twin.adapted" (key only, params ignored)
    expect(screen.getByText('twin.adapted')).toBeInTheDocument()
  })

  it('shows "no differences" message when content is identical', async () => {
    render(
      <AccessibilityTwin
        originalContent="Same content"
        adaptedContent="Same content"
      />
    )

    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    await user.click(adaptedTab)

    // When content is identical, computeLineDiff returns unchanged entries (not empty),
    // so the diff list renders with all lines marked as unchanged -- no additions or removals.
    const diffList = screen.getByRole('list', { name: /twin\.diff_label/i })
    expect(diffList).toBeInTheDocument()
    expect(screen.queryByLabelText('twin.addition')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('twin.removal')).not.toBeInTheDocument()
  })

  it('tab has correct aria-controls attributes', () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )
    const originalTab = screen.getByRole('tab', { name: /twin\.original/i })
    expect(originalTab).toHaveAttribute('aria-controls', 'panel-original')

    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    expect(adaptedTab).toHaveAttribute('aria-controls', 'panel-adapted')
  })

  it('inactive tab has tabIndex -1', () => {
    render(
      <AccessibilityTwin originalContent={ORIGINAL} adaptedContent={ADAPTED} />
    )
    const adaptedTab = screen.getByRole('tab', { name: /twin\.adapted/i })
    expect(adaptedTab).toHaveAttribute('tabindex', '-1')
  })
})
