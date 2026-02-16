import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanHistoryCard, type TraceRecord } from './plan-history-card'

const completedTrace: TraceRecord = {
  run_id: 'aaaa-1111-bbbb-2222',
  status: 'completed',
  total_time_ms: 4500,
  node_count: 8,
  final_score: 85,
  model_used: 'claude-haiku-4-5',
  refinement_count: 1,
}

const failedTrace: TraceRecord = {
  run_id: 'cccc-3333-dddd-4444',
  status: 'failed',
  total_time_ms: 1200,
  node_count: 3,
  final_score: null,
  model_used: 'gpt-5.2',
  refinement_count: 0,
}

// Mock useTranslations return type
const t = ((key: string) => `dashboard.${key}`) as ReturnType<
  typeof import('next-intl').useTranslations<'dashboard'>
>

describe('PlanHistoryCard', () => {
  it('renders without crashing', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByRole('link')).toBeInTheDocument()
  })

  it('renders as a link to plans page', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/en/plans')
  })

  it('shows shortened run_id (first 8 chars)', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByText('aaaa-111')).toBeInTheDocument()
  })

  it('shows completed status badge', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByText('dashboard.plan_status_completed')).toBeInTheDocument()
  })

  it('shows failed status badge for failed trace', () => {
    render(<PlanHistoryCard trace={failedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByText('dashboard.plan_status_failed')).toBeInTheDocument()
  })

  it('shows model used', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByText('claude-haiku-4-5')).toBeInTheDocument()
  })

  it('formats time in seconds', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    // 4500ms => 4.5s
    expect(screen.getByText(/4\.5s/)).toBeInTheDocument()
  })

  it('shows final score when present', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    expect(screen.getByText(/85/)).toBeInTheDocument()
  })

  it('does not show score when null', () => {
    const { container } = render(
      <PlanHistoryCard trace={failedTrace} localePrefix="/en" t={t} />
    )
    // Only the time row should be present, not score
    const text = container.textContent ?? ''
    expect(text).not.toContain('dashboard.plan_score')
  })

  it('uses glass card styling', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/en" t={t} />)
    const link = screen.getByRole('link')
    expect(link.className).toContain('glass')
    expect(link.className).toContain('card-hover')
  })

  it('uses correct locale prefix for link', () => {
    render(<PlanHistoryCard trace={completedTrace} localePrefix="/pt-BR" t={t} />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/pt-BR/plans')
  })
})
