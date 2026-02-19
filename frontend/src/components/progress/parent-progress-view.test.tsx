import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ParentProgressView } from './parent-progress-view'

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, transition: _t, variants: _v, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
}))

// Mock child components
vi.mock('@/components/shared/empty-state', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}))

vi.mock('@/components/shared/skeleton', () => ({
  SkeletonCard: () => <div data-testid="skeleton-card" />,
}))

vi.mock('./student-progress-card', () => ({
  StudentProgressCard: ({ student }: { student: { student_name: string } }) => (
    <div data-testid="student-card">{student.student_name}</div>
  ),
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

function makeParentData(overrides: Record<string, unknown> = {}) {
  return {
    parent_id: 'p1',
    children: [
      {
        student_id: 's1',
        student_name: 'Emma',
        standards_count: 5,
        mastered_count: 3,
        proficient_count: 1,
        developing_count: 1,
        last_activity: '2026-02-14T10:00:00Z',
      },
      {
        student_id: 's2',
        student_name: 'Lucas',
        standards_count: 5,
        mastered_count: 1,
        proficient_count: 2,
        developing_count: 2,
        last_activity: '2026-02-13T15:00:00Z',
      },
    ],
    ...overrides,
  }
}

describe('ParentProgressView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeletons initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    render(<ParentProgressView />)
    const skeletons = screen.getAllByTestId('skeleton-card')
    expect(skeletons.length).toBeGreaterThanOrEqual(2)
  })

  it('shows loading container with aria-busy', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { container } = render(<ParentProgressView />)
    const busyEl = container.querySelector('[aria-busy="true"]')
    expect(busyEl).toBeInTheDocument()
  })

  it('shows empty state when no children linked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeParentData({ children: [] }),
    })
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    })
  })

  it('shows error state on fetch failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    })
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('shows error state on network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('shows retry button on error', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByText('progress.retry')).toBeInTheDocument()
    })
  })

  it('renders children progress cards after successful fetch', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeParentData(),
    })
    render(<ParentProgressView />)
    await waitFor(() => {
      const cards = screen.getAllByTestId('student-card')
      expect(cards.length).toBe(2)
      expect(screen.getByText('Emma')).toBeInTheDocument()
      expect(screen.getByText('Lucas')).toBeInTheDocument()
    })
  })

  it('renders subtitle with child count', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeParentData(),
    })
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByText('progress.parent_subtitle')).toBeInTheDocument()
    })
  })

  it('calls fetch with parent endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeParentData(),
    })
    render(<ParentProgressView />)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/progress/parent')
  })

  it('renders single child without 2-column grid', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeParentData({
          children: [
            {
              student_id: 's1',
              student_name: 'Emma',
              standards_count: 5,
              mastered_count: 3,
              proficient_count: 1,
              developing_count: 1,
              last_activity: null,
            },
          ],
        }),
    })
    const { container } = render(<ParentProgressView />)
    await waitFor(() => {
      expect(screen.getByText('Emma')).toBeInTheDocument()
    })
    const grid = container.querySelector('.grid')
    expect(grid?.className).toContain('max-w-md')
  })
})
