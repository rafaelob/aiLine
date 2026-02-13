import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ExportsPage from './page'

vi.mock('motion/react', () => {
  function stripMotionProps(rest: Record<string, unknown>) {
    const { initial: _i, animate: _a, transition: _t, layoutId: _l, ...safe } = rest
    return safe
  }
  return {
    motion: {
      div: ({ children, ...rest }: Record<string, unknown>) => {
        return <div {...stripMotionProps(rest)}>{children as React.ReactNode}</div>
      },
      li: ({ children, ...rest }: Record<string, unknown>) => {
        return <li {...stripMotionProps(rest)}>{children as React.ReactNode}</li>
      },
      article: ({ children, ...rest }: Record<string, unknown>) => {
        return <article {...stripMotionProps(rest)}>{children as React.ReactNode}</article>
      },
    },
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }
})

vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

// Track what searchParams returns
let mockPlanId: string | null = null

vi.mock('next/navigation', async () => {
  const actual = await vi.importActual('next/navigation')
  return {
    ...actual as object,
    usePathname: () => '/pt-BR/exports',
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    }),
    useParams: () => ({ locale: 'pt-BR' }),
    useSearchParams: () => ({
      get: (key: string) => {
        if (key === 'planId') return mockPlanId
        return null
      },
    }),
  }
})

const MOCK_API_RESPONSE = {
  plan_title: 'Frações e Números Decimais',
  exports: {
    standard: '<h1>Frações e Números Decimais</h1><p>Content here</p>',
    low_distraction: '<h1>Frações e Números Decimais</h1><p>Simplified</p>',
    large_print: '<h1>Large Print</h1>',
    high_contrast: '<div>High contrast content</div>',
    dyslexia_friendly: '<div>Dyslexia friendly content</div>',
    screen_reader: '<article>Screen reader content</article>',
    visual_schedule: 'visual_schedule',
  },
  schedule_steps: [
    {
      stepNumber: 1,
      title: 'Roda de Conversa',
      description: 'Discussão sobre frações.',
      durationMinutes: 15,
      type: 'intro',
      materials: ['Quadro branco'],
      adaptations: ['Usar imagens para TEA'],
    },
  ],
}

describe('ExportsPage', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockPlanId = null
    vi.stubGlobal('fetch', vi.fn())
  })

  it('renders the page heading', () => {
    render(<ExportsPage />)
    expect(screen.getByText('exports.title')).toBeInTheDocument()
  })

  it('renders description text', () => {
    render(<ExportsPage />)
    expect(
      screen.getByText('exports.description')
    ).toBeInTheDocument()
  })

  it('shows empty state when no planId is provided', () => {
    render(<ExportsPage />)
    expect(
      screen.getByText('exports.no_plan')
    ).toBeInTheDocument()
  })

  it('shows loading state while fetching', async () => {
    mockPlanId = 'plan-123'
    // fetch never resolves
    vi.mocked(fetch).mockReturnValue(new Promise(() => {}))

    render(<ExportsPage />)

    expect(screen.getByText('common.loading')).toBeInTheDocument()
  })

  it('shows error state on fetch failure', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'))

    render(<ExportsPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('renders retry button on error', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'))

    render(<ExportsPage />)

    await waitFor(() => {
      expect(screen.getByText('common.retry')).toBeInTheDocument()
    })
  })

  it('renders sidebar and content on successful fetch', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_API_RESPONSE,
    } as Response)

    render(<ExportsPage />)

    await waitFor(() => {
      expect(screen.getByLabelText('exports.variants_aria_label')).toBeInTheDocument()
    })
  })

  it('renders variant buttons in sidebar after fetch', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_API_RESPONSE,
    } as Response)

    render(<ExportsPage />)

    await waitFor(() => {
      const sidebar = screen.getByLabelText('exports.variants_aria_label')
      expect(sidebar).toBeInTheDocument()
    })

    const sidebar = screen.getByLabelText('exports.variants_aria_label')
    expect(within(sidebar).getByText('export_variants.standard')).toBeInTheDocument()
    expect(within(sidebar).getByText('export_variants.low_distraction')).toBeInTheDocument()
    expect(within(sidebar).getByText('export_variants.large_print')).toBeInTheDocument()
  })

  it('shows error on HTTP error status', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 404,
    } as Response)

    render(<ExportsPage />)

    await waitFor(() => {
      expect(screen.getByText('HTTP 404')).toBeInTheDocument()
    })
  })

  it('switches to visual schedule when that variant is selected', async () => {
    mockPlanId = 'plan-123'
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_API_RESPONSE,
    } as Response)

    render(<ExportsPage />)

    await waitFor(() => {
      expect(screen.getByLabelText('exports.variants_aria_label')).toBeInTheDocument()
    })

    const sidebar = screen.getByLabelText('exports.variants_aria_label')
    const visualScheduleButton = within(sidebar).getByText('export_variants.visual_schedule').closest('button')
    if (visualScheduleButton) {
      await user.click(visualScheduleButton)
      expect(screen.getByText('Frações e Números Decimais')).toBeInTheDocument()
    }
  })
})
