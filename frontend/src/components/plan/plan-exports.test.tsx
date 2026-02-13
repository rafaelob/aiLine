import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PlanExports } from './plan-exports'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

// Mock fetch
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

describe('PlanExports', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ content: 'Export content here' }),
    })
  })

  it('renders the title', () => {
    render(<PlanExports planId="plan-1" />)
    expect(screen.getByText('exports.title')).toBeInTheDocument()
  })

  it('renders export variant buttons', () => {
    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(10)
  })

  it('no variant is selected initially', () => {
    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    for (const opt of options) {
      expect(opt).toHaveAttribute('aria-selected', 'false')
    }
  })

  it('selects a variant and fetches content on click', async () => {
    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    await user.click(options[0])

    expect(options[0]).toHaveAttribute('aria-selected', 'true')
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('displays fetched content', async () => {
    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    await user.click(options[0])

    expect(await screen.findByText('Export content here')).toBeInTheDocument()
  })

  it('shows loading state while fetching', async () => {
    let resolvePromise: (value: unknown) => void
    mockFetch.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )

    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    await user.click(options[0])

    expect(screen.getByText('plan_exports.loading')).toBeInTheDocument()

    // Resolve
    resolvePromise!({
      ok: true,
      json: async () => ({ content: 'Done' }),
    })
  })

  it('shows error message on fetch failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    render(<PlanExports planId="plan-1" />)
    const options = screen.getAllByRole('option')
    await user.click(options[0])

    expect(
      await screen.findByText('plan_exports.unavailable')
    ).toBeInTheDocument()
  })

  it('has accessible listbox', () => {
    render(<PlanExports planId="plan-1" />)
    const listbox = screen.getByRole('listbox', { name: 'exports.select' })
    expect(listbox).toBeInTheDocument()
  })
})
