import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MobileNav } from './mobile-nav'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, layoutId: _l, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  LayoutGroup: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('MobileNav', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders as a navigation landmark', () => {
    render(<MobileNav />)
    const nav = screen.getByRole('navigation', { name: /nav\.mobile_nav_label/i })
    expect(nav).toBeInTheDocument()
  })

  it('renders 4 primary navigation links', () => {
    render(<MobileNav />)
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(4)
  })

  it('renders primary nav labels', () => {
    render(<MobileNav />)
    expect(screen.getByText('nav.dashboard')).toBeInTheDocument()
    expect(screen.getByText('nav.plans')).toBeInTheDocument()
    expect(screen.getByText('nav.tutors')).toBeInTheDocument()
    expect(screen.getByText('nav.progress')).toBeInTheDocument()
  })

  it('renders the More button', () => {
    render(<MobileNav />)
    const moreButton = screen.getByRole('button', { name: /nav\.more_menu_label/i })
    expect(moreButton).toBeInTheDocument()
    expect(moreButton).toHaveAttribute('aria-expanded', 'false')
    expect(moreButton).toHaveAttribute('aria-haspopup', 'true')
  })

  it('shows overflow items when More is clicked', async () => {
    render(<MobileNav />)
    const moreButton = screen.getByRole('button', { name: /nav\.more_menu_label/i })

    await user.click(moreButton)

    expect(moreButton).toHaveAttribute('aria-expanded', 'true')
    const menu = screen.getByRole('menu')
    expect(menu).toBeInTheDocument()

    const menuItems = within(menu).getAllByRole('menuitem')
    expect(menuItems).toHaveLength(4)
  })

  it('overflow menu contains materials, sign language, observability, and settings', async () => {
    render(<MobileNav />)
    const moreButton = screen.getByRole('button', { name: /nav\.more_menu_label/i })
    await user.click(moreButton)

    const menu = screen.getByRole('menu')
    expect(within(menu).getByText('nav.materials')).toBeInTheDocument()
    expect(within(menu).getByText('nav.sign_language')).toBeInTheDocument()
    expect(within(menu).getByText('nav.observability')).toBeInTheDocument()
    expect(within(menu).getByText('nav.settings')).toBeInTheDocument()
  })

  it('dashboard link points to /dashboard', () => {
    render(<MobileNav />)
    const links = screen.getAllByRole('link')
    expect(links[0]).toHaveAttribute('href', '/pt-BR/dashboard')
  })

  it('toggles overflow menu closed on second click', async () => {
    render(<MobileNav />)
    const moreButton = screen.getByRole('button', { name: /nav\.more_menu_label/i })

    await user.click(moreButton)
    expect(screen.getByRole('menu')).toBeInTheDocument()

    await user.click(moreButton)
    expect(moreButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('total accessible destinations equals 8 (4 primary + 4 overflow)', async () => {
    render(<MobileNav />)
    const moreButton = screen.getByRole('button', { name: /nav\.more_menu_label/i })
    await user.click(moreButton)

    const allLinks = screen.getAllByRole('link')
    const menuItems = screen.getAllByRole('menuitem')
    expect(allLinks.length + menuItems.length).toBe(8)
  })
})
