import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PendingReviewsBadge } from './pending-reviews-badge'

// Mock motion/react to render static elements
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

function makeReview(overrides: Record<string, unknown> = {}) {
  return {
    review_id: 'rev-1',
    plan_id: 'plan-abc',
    teacher_id: 't1',
    status: 'pending_review',
    notes: '',
    approved_at: null,
    created_at: '2026-02-14T10:00:00Z',
    ...overrides,
  }
}

describe('PendingReviewsBadge', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when no pending reviews', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    const { container } = render(<PendingReviewsBadge />)

    // Wait for the fetch to complete and state to settle
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    // Component returns null when reviews.length === 0
    expect(container.innerHTML).toBe('')
  })

  it('renders badge count when reviews exist', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [makeReview(), makeReview({ review_id: 'rev-2', plan_id: 'plan-def' })],
    })

    render(<PendingReviewsBadge />)

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('renders pending label when reviews exist', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [makeReview()],
    })

    render(<PendingReviewsBadge />)

    await waitFor(() => {
      expect(screen.getByText('review.pending')).toBeInTheDocument()
    })
  })

  it('expands list on click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [makeReview()],
    })

    render(<PendingReviewsBadge />)

    // Wait for badge to appear
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const toggleButton = screen.getByRole('button', { expanded: false })
    await user.click(toggleButton)

    expect(toggleButton).toHaveAttribute('aria-expanded', 'true')
    // The list should now be visible with the plan_id
    expect(screen.getByText('plan-abc')).toBeInTheDocument()
  })

  it('displays review plan_id and date in expanded list', async () => {
    const reviews = [
      makeReview({ review_id: 'rev-1', plan_id: 'plan-abc', created_at: '2026-02-14T10:00:00Z' }),
      makeReview({ review_id: 'rev-2', plan_id: 'plan-xyz', created_at: '2026-02-13T08:00:00Z' }),
    ]
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => reviews,
    })

    render(<PendingReviewsBadge />)

    // Wait for badge to appear
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument()
    })

    // Expand the list
    await user.click(screen.getByRole('button'))

    // Plan IDs
    expect(screen.getByText('plan-abc')).toBeInTheDocument()
    expect(screen.getByText('plan-xyz')).toBeInTheDocument()

    // Dates are formatted via toLocaleDateString()
    const dateA = new Date('2026-02-14T10:00:00Z').toLocaleDateString()
    const dateB = new Date('2026-02-13T08:00:00Z').toLocaleDateString()
    expect(screen.getByText(dateA)).toBeInTheDocument()
    expect(screen.getByText(dateB)).toBeInTheDocument()
  })

  it('collapses list on second click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [makeReview()],
    })

    render(<PendingReviewsBadge />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const toggleButton = screen.getByRole('button')

    // Expand
    await user.click(toggleButton)
    expect(screen.getByText('plan-abc')).toBeInTheDocument()

    // Collapse
    await user.click(toggleButton)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('plan-abc')).not.toBeInTheDocument()
  })

  it('renders nothing when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })

    const { container } = render(<PendingReviewsBadge />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    // Component returns null on error (loaded=true but reviews=[])
    expect(container.innerHTML).toBe('')
  })

  it('calls fetch with correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    render(<PendingReviewsBadge />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/plans/pending-review')
  })
})
