import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ProgressDashboard } from './progress-dashboard'

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
  EmptyState: ({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) => (
    <div data-testid="empty-state">
      <p>{title}</p>
      <p>{description}</p>
      {action}
    </div>
  ),
}))

vi.mock('@/components/shared/skeleton', () => ({
  SkeletonCard: () => <div data-testid="skeleton-card" />,
}))

vi.mock('./progress-heatmap', () => ({
  ProgressHeatmap: () => <div data-testid="progress-heatmap" />,
}))

vi.mock('./student-progress-card', () => ({
  StudentProgressCard: ({ student }: { student: { student_name: string } }) => (
    <div data-testid="student-card">{student.student_name}</div>
  ),
}))

vi.mock('./record-progress-form', () => ({
  RecordProgressForm: ({ onSuccess }: { onSuccess: () => void }) => (
    <div data-testid="record-form">
      <button type="button" onClick={onSuccess}>Submit</button>
    </div>
  ),
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

function makeDashboardData(overrides: Record<string, unknown> = {}) {
  return {
    teacher_id: 't1',
    total_students: 3,
    total_standards: 2,
    mastery_distribution: {
      not_started: 0,
      developing: 2,
      proficient: 3,
      mastered: 1,
    },
    students: [
      {
        student_id: 's1',
        student_name: 'Alice',
        standards_count: 2,
        mastered_count: 1,
        proficient_count: 1,
        developing_count: 0,
        last_activity: '2026-02-14T10:00:00Z',
      },
      {
        student_id: 's2',
        student_name: 'Bob',
        standards_count: 2,
        mastered_count: 0,
        proficient_count: 1,
        developing_count: 1,
        last_activity: '2026-02-14T09:00:00Z',
      },
    ],
    standards: [
      {
        standard_code: 'EF06MA01',
        standard_description: 'Fractions',
        student_count: 3,
        mastered_count: 1,
        proficient_count: 1,
        developing_count: 1,
      },
    ],
    ...overrides,
  }
}

describe('ProgressDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeletons initially', () => {
    // Never resolve fetch so loading stays true
    mockFetch.mockReturnValue(new Promise(() => {}))
    render(<ProgressDashboard />)
    const skeletons = screen.getAllByTestId('skeleton-card')
    expect(skeletons.length).toBeGreaterThanOrEqual(4)
  })

  it('shows empty state when no data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData({ total_students: 0, students: [], standards: [] }),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    })
  })

  it('shows error state on fetch failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('shows error state on network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('shows retry button on error', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByText('progress.retry')).toBeInTheDocument()
    })
  })

  it('renders dashboard data after successful fetch', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      // Stat card labels
      expect(screen.getByText('progress.total_students')).toBeInTheDocument()
      expect(screen.getByText('progress.total_standards')).toBeInTheDocument()
      // total_students value (3 is unique)
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('renders student cards', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      const cards = screen.getAllByTestId('student-card')
      expect(cards.length).toBe(2)
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()
    })
  })

  it('renders standards heatmap when data has standards', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByTestId('progress-heatmap')).toBeInTheDocument()
    })
  })

  it('does not render heatmap when no standards', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData({ standards: [] }),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.queryByTestId('progress-heatmap')).not.toBeInTheDocument()
    })
  })

  it('renders mastery distribution labels', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      // mastery_levels.mastered appears twice (stat card + legend), use getAllByText
      const masteredLabels = screen.getAllByText('progress.mastery_levels.mastered')
      expect(masteredLabels.length).toBeGreaterThanOrEqual(1)
      const proficientLabels = screen.getAllByText('progress.mastery_levels.proficient')
      expect(proficientLabels.length).toBeGreaterThanOrEqual(1)
      const developingLabels = screen.getAllByText('progress.mastery_levels.developing')
      expect(developingLabels.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders record progress button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(screen.getByText('progress.record_progress')).toBeInTheDocument()
    })
  })

  it('calls fetch with correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeDashboardData(),
    })
    render(<ProgressDashboard />)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/progress/dashboard')
  })
})
