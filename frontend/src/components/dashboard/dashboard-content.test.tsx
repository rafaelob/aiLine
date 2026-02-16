import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DashboardContent } from './dashboard-content'

vi.mock('motion/react', () => ({
  motion: {
    a: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <a {...safe}>{children as React.ReactNode}</a>
    },
    section: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, style, variants: _v, className, ...safe } = rest
      return <section style={style as React.CSSProperties} className={className as string} {...safe}>{children as React.ReactNode}</section>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    h1: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <h1 {...safe}>{children as React.ReactNode}</h1>
    },
    p: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <p {...safe}>{children as React.ReactNode}</p>
    },
  },
  useMotionValue: () => ({ get: () => 0, set: () => {}, on: () => () => {} }),
  animate: () => ({ stop: () => {} }),
  useInView: () => false,
  useReducedMotion: () => false,
}))

/* ===== Fetch mock helpers ===== */

const MOCK_TRACES = [
  { run_id: 'aaaa-1111-bbbb-2222', status: 'completed', total_time_ms: 4500, node_count: 8, final_score: 85, model_used: 'claude-haiku-4-5', refinement_count: 1 },
  { run_id: 'cccc-3333-dddd-4444', status: 'completed', total_time_ms: 3200, node_count: 6, final_score: 72, model_used: 'gpt-5.2', refinement_count: 0 },
  { run_id: 'eeee-5555-ffff-6666', status: 'failed', total_time_ms: 1200, node_count: 3, final_score: null, model_used: 'gemini-3-pro', refinement_count: 0 },
]

const MOCK_PROGRESS = { students: [{ id: '1' }, { id: '2' }, { id: '3' }], standards: [] }

function mockFetchSuccess(traces = MOCK_TRACES, progress = MOCK_PROGRESS) {
  return vi.fn((url: string) => {
    if (url.includes('/traces/recent')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(traces) })
    }
    if (url.includes('/progress/dashboard')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(progress) })
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) })
  })
}

function mockFetchEmpty() {
  return mockFetchSuccess([], { students: [], standards: [] })
}

function mockFetchError() {
  return vi.fn(() => Promise.reject(new Error('Network error')))
}

/* ===== Tests ===== */

describe('DashboardContent', () => {
  beforeEach(() => {
    // Default: empty API responses so existing tests keep passing with 0 values
    vi.stubGlobal('fetch', mockFetchEmpty())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders welcome heading', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toBeInTheDocument()
      expect(heading.textContent).toBe('dashboard.title')
    })
  })

  it('renders quick actions section', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.quick_actions')).toBeInTheDocument()
    })
  })

  it('renders quick action links, view-all, and empty CTA', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      // 3 quick actions + 1 "view all" + 1 empty CTA = 5
      expect(links.length).toBeGreaterThanOrEqual(5)
    })
  })

  it('uses bento grid layout with 3-column stats grid', async () => {
    const { container } = render(<DashboardContent />)
    await waitFor(() => {
      const gridEl = container.querySelector('.grid')
      expect(gridEl).toBeInTheDocument()
      expect(gridEl?.className).toContain('md:grid-cols-3')
    })
  })

  it('renders stat cards', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.stat_plans')).toBeInTheDocument()
      expect(screen.getByText('dashboard.stat_students')).toBeInTheDocument()
      expect(screen.getByText('dashboard.stat_score')).toBeInTheDocument()
    })
  })

  it('renders recent plans section', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.recent_plans')).toBeInTheDocument()
    })
  })

  it('shows no plans message when empty', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.no_plans')).toBeInTheDocument()
    })
  })

  it('renders empty CTA button', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.empty_cta')).toBeInTheDocument()
    })
  })

  it('renders view all link', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.view_all')).toBeInTheDocument()
    })
  })

  it('quick actions have correct href with locale prefix', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      const hrefs = links.map((link) => link.getAttribute('href'))
      expect(hrefs.some((h) => h?.includes('/plans'))).toBe(true)
    })
  })

  it('renders action labels from translations', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.create_plan')).toBeInTheDocument()
      expect(screen.getByText('dashboard.upload_material')).toBeInTheDocument()
      expect(screen.getByText('dashboard.start_tutor')).toBeInTheDocument()
    })
  })

  it('renders section with accessible heading', async () => {
    render(<DashboardContent />)
    await waitFor(() => {
      const heading = document.getElementById('quick-actions-heading')
      expect(heading).toBeInTheDocument()
      expect(heading?.textContent).toBe('dashboard.quick_actions')
    })
  })

  /* ===== New tests for live API data ===== */

  it('shows loading skeleton while fetching', () => {
    // Use a fetch that never resolves
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    const { container } = render(<DashboardContent />)
    const skeleton = container.querySelector('[data-testid="loading-skeleton"]')
    expect(skeleton).toBeInTheDocument()
    const pulseCards = skeleton?.querySelectorAll('.animate-pulse')
    expect(pulseCards?.length).toBe(3)
  })

  it('renders plan count from API', async () => {
    vi.stubGlobal('fetch', mockFetchSuccess())
    render(<DashboardContent />)
    await waitFor(() => {
      // 3 traces = plan count should show "3" via AnimatedCounter
      // AnimatedCounter renders {value}{suffix} in the span
      const statLabels = screen.getAllByText('dashboard.stat_plans')
      expect(statLabels.length).toBe(1)
      // The parent stat card should contain the numeric value
      const statCard = statLabels[0].closest('.gradient-border-glass')
      expect(statCard).toBeInTheDocument()
      expect(statCard?.textContent).toContain('3')
    })
  })

  it('renders student count from API', async () => {
    vi.stubGlobal('fetch', mockFetchSuccess())
    render(<DashboardContent />)
    await waitFor(() => {
      const statLabels = screen.getAllByText('dashboard.stat_students')
      expect(statLabels.length).toBe(1)
      const statCard = statLabels[0].closest('.gradient-border-glass')
      expect(statCard).toBeInTheDocument()
      expect(statCard?.textContent).toContain('3')
    })
  })

  it('renders plan history cards when traces exist', async () => {
    vi.stubGlobal('fetch', mockFetchSuccess())
    const { container } = render(<DashboardContent />)
    await waitFor(() => {
      const grid = container.querySelector('[data-testid="plan-history-grid"]')
      expect(grid).toBeInTheDocument()
      // 3 traces = 3 cards
      const cards = grid?.querySelectorAll('.glass.card-hover')
      expect(cards?.length).toBe(3)
    })
  })

  it('shows empty state when no traces', async () => {
    vi.stubGlobal('fetch', mockFetchEmpty())
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.no_plans')).toBeInTheDocument()
      expect(screen.getByText('dashboard.empty_cta')).toBeInTheDocument()
    })
  })

  it('handles fetch error by showing demo data fallback', async () => {
    vi.stubGlobal('fetch', mockFetchError())
    const { container } = render(<DashboardContent />)
    await waitFor(() => {
      // Should still render stat cards — no crash
      expect(screen.getByText('dashboard.stat_plans')).toBeInTheDocument()
      // Demo traces should populate plan history grid (6 demo traces)
      const grid = container.querySelector('[data-testid="plan-history-grid"]')
      expect(grid).toBeInTheDocument()
      const cards = grid?.querySelectorAll('.glass.card-hover')
      expect(cards?.length).toBe(6)
    })
  })

  it('shows demo mode banner when API is offline', async () => {
    vi.stubGlobal('fetch', mockFetchError())
    render(<DashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('dashboard.demo_mode')).toBeInTheDocument()
    })
  })

  it('renders plan status badges', async () => {
    vi.stubGlobal('fetch', mockFetchSuccess())
    render(<DashboardContent />)
    await waitFor(() => {
      // 2 completed + 1 failed
      const completedBadges = screen.getAllByText('dashboard.plan_status_completed')
      expect(completedBadges.length).toBe(2)
      const failedBadges = screen.getAllByText('dashboard.plan_status_failed')
      expect(failedBadges.length).toBe(1)
    })
  })

  it('renders plan time and score in cards', async () => {
    vi.stubGlobal('fetch', mockFetchSuccess())
    const { container } = render(<DashboardContent />)
    await waitFor(() => {
      const grid = container.querySelector('[data-testid="plan-history-grid"]')
      expect(grid).toBeInTheDocument()
      // First trace: 4500ms => "4.5s"
      expect(grid?.textContent).toContain('4.5s')
      // First trace score: 85
      expect(grid?.textContent).toContain('85')
    })
  })

  it('shows max 6 plan cards', async () => {
    const manyTraces = Array.from({ length: 10 }, (_, i) => ({
      run_id: `run-${i}-xxxx-yyyy-zzzz`,
      status: 'completed',
      total_time_ms: 2000,
      node_count: 5,
      final_score: 80,
      model_used: 'claude-haiku-4-5',
      refinement_count: 0,
    }))
    vi.stubGlobal('fetch', mockFetchSuccess(manyTraces))
    const { container } = render(<DashboardContent />)
    await waitFor(() => {
      const grid = container.querySelector('[data-testid="plan-history-grid"]')
      expect(grid).toBeInTheDocument()
      const cards = grid?.querySelectorAll('.glass.card-hover')
      expect(cards?.length).toBe(6)
    })
  })
})
