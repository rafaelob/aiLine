import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar } from './sidebar'

vi.mock('motion/react', () => ({
  motion: {
    aside: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <aside {...safe}>{children as React.ReactNode}</aside>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
    svg: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <svg {...safe}>{children as React.ReactNode}</svg>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('Sidebar', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders as a navigation landmark', () => {
    render(<Sidebar />)
    const nav = screen.getByRole('navigation', { name: 'nav.main_nav_label' })
    expect(nav).toBeInTheDocument()
  })

  it('renders the AiLine brand name', () => {
    render(<Sidebar />)
    expect(screen.getByText('AiLine')).toBeInTheDocument()
  })

  it('renders all navigation items', () => {
    render(<Sidebar />)
    expect(screen.getByText('nav.dashboard')).toBeInTheDocument()
    expect(screen.getByText('nav.plans')).toBeInTheDocument()
    expect(screen.getByText('nav.materials')).toBeInTheDocument()
    expect(screen.getByText('nav.tutors')).toBeInTheDocument()
    expect(screen.getByText('nav.settings')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<Sidebar />)
    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThanOrEqual(5)
  })

  it('marks the dashboard as active on root path', () => {
    render(<Sidebar />)
    const dashLink = screen.getAllByRole('link')[0]
    expect(dashLink).toHaveAttribute('aria-current', 'page')
  })

  it('renders collapse toggle button', () => {
    render(<Sidebar />)
    const collapseButton = screen.getByLabelText('nav.collapse')
    expect(collapseButton).toBeInTheDocument()
  })

  it('toggles collapse state on button click', async () => {
    render(<Sidebar />)
    const collapseButton = screen.getByLabelText('nav.collapse')
    await user.click(collapseButton)

    // After collapse, label changes to expand
    expect(screen.getByLabelText('nav.expand')).toBeInTheDocument()
  })

  it('shows brand name when not collapsed', () => {
    render(<Sidebar />)
    expect(screen.getByText('AiLine')).toBeInTheDocument()
  })

  it('shows nav labels when not collapsed', () => {
    render(<Sidebar />)
    expect(screen.getByText('nav.dashboard')).toBeInTheDocument()
    expect(screen.getByText('nav.plans')).toBeInTheDocument()
  })
})
