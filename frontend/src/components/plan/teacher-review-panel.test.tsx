import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TeacherReviewPanel } from './teacher-review-panel'

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, transition: _t, exit: _e, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
    tr: ({ children, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <tr {...rest}>{children as React.ReactNode}</tr>
    },
    p: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, ...rest }: Record<string, unknown>) => {
      return <p {...rest}>{children as React.ReactNode}</p>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

function makeReviewData(overrides: Record<string, unknown> = {}) {
  return {
    review_id: 'rev-1',
    plan_id: 'plan-1',
    teacher_id: 't1',
    status: 'pending_review',
    notes: '',
    approved_at: null,
    created_at: '2026-02-14T10:00:00Z',
    ...overrides,
  }
}

describe('TeacherReviewPanel', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the panel title', () => {
    render(<TeacherReviewPanel planId="plan-1" />)
    expect(screen.getByText('review.title')).toBeInTheDocument()
  })

  it('renders status badge with pending status', () => {
    render(<TeacherReviewPanel planId="plan-1" />)
    expect(screen.getByText('review.pending')).toBeInTheDocument()
  })

  it('renders approve, revision, and reject buttons', () => {
    render(<TeacherReviewPanel planId="plan-1" />)
    expect(screen.getByText('review.approve')).toBeInTheDocument()
    expect(screen.getByText('review.request_revision')).toBeInTheDocument()
    expect(screen.getByText('review.reject')).toBeInTheDocument()
  })

  it('renders notes textarea', () => {
    render(<TeacherReviewPanel planId="plan-1" />)
    const textarea = screen.getByRole('textbox', { name: 'review.notes_placeholder' })
    expect(textarea).toBeInTheDocument()
  })

  it('submits approve review on approve click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeReviewData({ status: 'approved', approved_at: '2026-02-14T12:00:00Z' }),
    })
    const onReviewSubmitted = vi.fn()
    render(<TeacherReviewPanel planId="plan-1" onReviewSubmitted={onReviewSubmitted} />)

    await user.click(screen.getByText('review.approve'))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/plans/plan-1/review')
    expect(options.method).toBe('POST')
    const body = JSON.parse(options.body)
    expect(body.status).toBe('approved')
  })

  it('submits reject review on reject click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeReviewData({ status: 'rejected', approved_at: '2026-02-14T12:00:00Z' }),
    })
    render(<TeacherReviewPanel planId="plan-1" />)

    await user.click(screen.getByText('review.reject'))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.status).toBe('rejected')
  })

  it('submits needs_revision review', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeReviewData({ status: 'needs_revision' }),
    })
    render(<TeacherReviewPanel planId="plan-1" />)

    await user.click(screen.getByText('review.request_revision'))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.status).toBe('needs_revision')
  })

  it('includes notes in the submission', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeReviewData({ status: 'approved', notes: 'Great work!' }),
    })
    render(<TeacherReviewPanel planId="plan-1" />)

    const textarea = screen.getByRole('textbox', { name: 'review.notes_placeholder' })
    await user.type(textarea, 'Great work!')
    await user.click(screen.getByText('review.approve'))

    await waitFor(() => {
      const body = JSON.parse(mockFetch.mock.calls[0][1].body)
      expect(body.notes).toBe('Great work!')
    })
  })

  it('shows error alert on submission failure', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    render(<TeacherReviewPanel planId="plan-1" />)

    await user.click(screen.getByText('review.approve'))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('shows finalized view when status is approved', () => {
    const review = makeReviewData({
      status: 'approved',
      notes: 'Excellent plan.',
      approved_at: '2026-02-14T12:00:00Z',
    })
    render(<TeacherReviewPanel planId="plan-1" initialReview={review} />)

    // Buttons should NOT be present
    expect(screen.queryByText('review.approve')).not.toBeInTheDocument()
    expect(screen.queryByText('review.reject')).not.toBeInTheDocument()
    // Notes should show
    expect(screen.getByText('Excellent plan.')).toBeInTheDocument()
  })

  it('shows finalized view when status is rejected', () => {
    const review = makeReviewData({
      status: 'rejected',
      notes: 'Not adequate.',
      approved_at: '2026-02-14T12:00:00Z',
    })
    render(<TeacherReviewPanel planId="plan-1" initialReview={review} />)

    expect(screen.queryByText('review.approve')).not.toBeInTheDocument()
    expect(screen.getByText('Not adequate.')).toBeInTheDocument()
  })

  it('hides buttons after successful approval submission', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeReviewData({ status: 'approved', approved_at: '2026-02-14T12:00:00Z' }),
    })
    render(<TeacherReviewPanel planId="plan-1" />)

    // Buttons initially visible
    expect(screen.getByText('review.approve')).toBeInTheDocument()

    await user.click(screen.getByText('review.approve'))

    await waitFor(() => {
      expect(screen.queryByText('review.approve')).not.toBeInTheDocument()
      expect(screen.queryByText('review.reject')).not.toBeInTheDocument()
    })
  })

  it('applies custom className', () => {
    const { container } = render(
      <TeacherReviewPanel planId="plan-1" className="custom-class" />
    )
    const div = container.firstElementChild
    expect(div?.className).toContain('custom-class')
  })

  it('pre-fills notes from initialReview', () => {
    const review = makeReviewData({ status: 'needs_revision', notes: 'Fix objectives' })
    render(<TeacherReviewPanel planId="plan-1" initialReview={review} />)

    const textarea = screen.getByRole('textbox', { name: 'review.notes_placeholder' })
    expect(textarea).toHaveValue('Fix objectives')
  })

  it('calls onReviewSubmitted callback after successful submission', async () => {
    const submittedReview = makeReviewData({ status: 'approved', approved_at: '2026-02-14T12:00:00Z' })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => submittedReview,
    })
    const onReviewSubmitted = vi.fn()
    render(<TeacherReviewPanel planId="plan-1" onReviewSubmitted={onReviewSubmitted} />)

    await user.click(screen.getByText('review.approve'))

    await waitFor(() => {
      expect(onReviewSubmitted).toHaveBeenCalledTimes(1)
      expect(onReviewSubmitted).toHaveBeenCalledWith(submittedReview)
    })
  })
})
