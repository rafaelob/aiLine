import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ConversationReview } from './conversation-review'

// Mock motion/react to render static elements
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock shared components
vi.mock('@/components/shared/empty-state', () => ({
  EmptyState: ({ title }: { title: string }) => <div data-testid="empty-state">{title}</div>,
}))

vi.mock('@/components/shared/skeleton', () => ({
  SkeletonCard: () => <div data-testid="skeleton-card">Loading...</div>,
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

function makeTranscript(overrides: Record<string, unknown> = {}) {
  return {
    session_id: 'sess-1',
    tutor_id: 'tutor-1',
    messages: [
      { role: 'user', content: 'Hello, can you help me?', created_at: '2026-02-14T10:00:00Z' },
      { role: 'assistant', content: 'Of course! What do you need?', created_at: '2026-02-14T10:00:05Z' },
    ],
    flags: [],
    created_at: '2026-02-14T10:00:00Z',
    ...overrides,
  }
}

describe('ConversationReview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton initially', () => {
    // Never resolve so loading stays true
    mockFetch.mockReturnValue(new Promise(() => {}))

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    expect(screen.getByTestId('skeleton-card')).toBeInTheDocument()
  })

  it('shows empty state when no messages', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript({ messages: [] }),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    })

    expect(screen.getByText('review.empty_title')).toBeInTheDocument()
  })

  it('shows empty state when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    })
  })

  it('renders transcript heading when data loaded', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      expect(screen.getByText('review.transcript')).toBeInTheDocument()
    })
  })

  it('renders messages from transcript', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      expect(screen.getByText('Hello, can you help me?')).toBeInTheDocument()
      expect(screen.getByText('Of course! What do you need?')).toBeInTheDocument()
    })
  })

  it('renders messages within a log role container', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      const logContainer = screen.getByRole('log')
      expect(logContainer).toBeInTheDocument()
    })
  })

  it('calls fetch with correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/tutors/tutor-1/sessions/sess-1/transcript')
  })

  it('applies custom className', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    const { container } = render(
      <ConversationReview tutorId="tutor-1" sessionId="sess-1" className="custom-class" />,
    )

    await waitFor(() => {
      expect(screen.getByText('review.transcript')).toBeInTheDocument()
    })

    const outerDiv = container.firstElementChild
    expect(outerDiv?.className).toContain('custom-class')
  })

  it('renders message timestamps', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeTranscript(),
    })

    render(<ConversationReview tutorId="tutor-1" sessionId="sess-1" />)

    const timeA = new Date('2026-02-14T10:00:00Z').toLocaleTimeString()
    const timeB = new Date('2026-02-14T10:00:05Z').toLocaleTimeString()

    await waitFor(() => {
      expect(screen.getByText(timeA)).toBeInTheDocument()
      expect(screen.getByText(timeB)).toBeInTheDocument()
    })
  })
})
