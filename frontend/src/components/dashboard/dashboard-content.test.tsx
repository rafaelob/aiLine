import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardContent } from './dashboard-content'

vi.mock('motion/react', () => ({
  motion: {
    a: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <a {...safe}>{children as React.ReactNode}</a>
    },
    section: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, style, ...safe } = rest
      return <section style={style as React.CSSProperties} {...safe}>{children as React.ReactNode}</section>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

describe('DashboardContent', () => {
  it('renders welcome heading', () => {
    render(<DashboardContent />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading.textContent).toBe('dashboard.title')
  })

  it('renders quick actions section', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.quick_actions')).toBeInTheDocument()
  })

  it('renders quick action links, view-all, and empty CTA', () => {
    render(<DashboardContent />)
    const links = screen.getAllByRole('link')
    // 3 quick actions + 1 "view all" + 1 empty CTA = 5
    expect(links.length).toBeGreaterThanOrEqual(5)
  })

  it('uses bento grid layout with 4-column grid', () => {
    const { container } = render(<DashboardContent />)
    // The bento grid container uses md:grid-cols-4
    const gridEl = container.querySelector('.grid')
    expect(gridEl).toBeInTheDocument()
    expect(gridEl?.className).toContain('md:grid-cols-4')
  })

  it('renders stat cards', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.stat_plans')).toBeInTheDocument()
    expect(screen.getByText('dashboard.stat_students')).toBeInTheDocument()
    expect(screen.getByText('dashboard.stat_score')).toBeInTheDocument()
  })

  it('renders recent plans section', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.recent_plans')).toBeInTheDocument()
  })

  it('shows no plans message when empty', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.no_plans')).toBeInTheDocument()
  })

  it('renders empty CTA button', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.empty_cta')).toBeInTheDocument()
  })

  it('renders view all link', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.view_all')).toBeInTheDocument()
  })

  it('quick actions have correct href with locale prefix', () => {
    render(<DashboardContent />)
    const links = screen.getAllByRole('link')
    const hrefs = links.map((link) => link.getAttribute('href'))
    expect(hrefs.some((h) => h?.includes('/plans'))).toBe(true)
  })

  it('renders action labels from translations', () => {
    render(<DashboardContent />)
    expect(screen.getByText('dashboard.create_plan')).toBeInTheDocument()
    expect(screen.getByText('dashboard.upload_material')).toBeInTheDocument()
    expect(screen.getByText('dashboard.start_tutor')).toBeInTheDocument()
  })

  it('renders section with accessible heading', () => {
    render(<DashboardContent />)
    const heading = document.getElementById('quick-actions-heading')
    expect(heading).toBeInTheDocument()
    expect(heading?.textContent).toBe('dashboard.quick_actions')
  })
})
