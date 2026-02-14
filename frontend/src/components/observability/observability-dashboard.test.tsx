import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ObservabilityDashboardContent from './observability-dashboard'
import type { ObservabilityDashboard } from '@/types/trace'

const mockData: ObservabilityDashboard = {
  provider: 'Anthropic',
  model: 'claude-haiku-4-5-20251001',
  scores: {
    quality_avg: 82.5,
    latency_p50_ms: 320,
    latency_p95_ms: 1200,
  },
  error_rate: 0.023,
  circuit_breaker_state: 'closed',
  sse_event_counts: {
    'stage.started': 45,
    'stage.completed': 42,
    'quality.scored': 38,
    'run.completed': 35,
  },
  token_usage: {
    input_tokens: 125000,
    output_tokens: 48000,
    estimated_cost_usd: 0.0854,
  },
  latency_history: [
    { timestamp: '2026-02-13T10:00:00Z', p50: 300, p95: 1100 },
    { timestamp: '2026-02-13T10:01:00Z', p50: 320, p95: 1200 },
  ],
}

describe('ObservabilityDashboardContent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    const { container } = render(<ObservabilityDashboardContent />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(1)
    vi.unstubAllGlobals()
  })

  it('renders provider name after successful fetch', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('Anthropic')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders latency values', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('320ms')).toBeInTheDocument()
      expect(screen.getByText('1200ms')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders error rate', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('2.3%')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders circuit breaker state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('observability.cb_closed')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders token usage', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('125,000')).toBeInTheDocument()
      expect(screen.getByText('48,000')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('shows error state on fetch failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('shows SSE event counts', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('stage.started')).toBeInTheDocument()
      expect(screen.getByText('45')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders retry button on error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('observability.retry')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('calls fetch again when retry button is clicked', async () => {
    const mockFetch = vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
    vi.stubGlobal('fetch', mockFetch)

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('observability.retry')).toBeInTheDocument()
    })

    const { default: userEvent } = await import('@testing-library/user-event')
    const user = userEvent.setup()
    await user.click(screen.getByText('observability.retry'))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    vi.unstubAllGlobals()
  })

  it('renders open circuit breaker state', async () => {
    const openData = { ...mockData, circuit_breaker_state: 'open' as const }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(openData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('observability.cb_open')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders half_open circuit breaker state', async () => {
    const halfOpenData = { ...mockData, circuit_breaker_state: 'half_open' as const }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(halfOpenData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('observability.cb_half_open')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders quality average score', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('82.5')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders model name', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('claude-haiku-4-5-20251001')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders estimated cost', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('$0.0854')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('shows error for non-ok HTTP response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
    }))

    render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText(/HTTP 503/)).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('renders latency sparkline when history is present', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const { container } = render(<ObservabilityDashboardContent />)
    await waitFor(() => {
      expect(screen.getByText('Anthropic')).toBeInTheDocument()
    })

    // Sparkline bars should be rendered (aria-hidden container with flex items)
    const sparklineBars = container.querySelectorAll('.rounded-t')
    expect(sparklineBars.length).toBeGreaterThan(0)

    vi.unstubAllGlobals()
  })
})
