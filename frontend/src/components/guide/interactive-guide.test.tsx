import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InteractiveGuide } from './interactive-guide'

// Mock motion/react — pass through DOM props, strip motion-specific ones
vi.mock('motion/react', () => ({
  motion: {
    div: ({
      children,
      layout: _l,
      layoutId: _li,
      initial: _i,
      animate: _a,
      exit: _e,
      transition: _t,
      variants: _v,
      ...rest
    }: Record<string, unknown>) => <div {...rest}>{children as React.ReactNode}</div>,
    span: ({
      children,
      layout: _l,
      layoutId: _li,
      initial: _i,
      animate: _a,
      exit: _e,
      transition: _t,
      style: _s,
      variants: _v,
      ...rest
    }: Record<string, unknown>) => (
      <span data-testid="active-indicator" {...rest}>
        {children as React.ReactNode}
      </span>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
}))

describe('InteractiveGuide', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page title', () => {
    render(<InteractiveGuide />)
    expect(screen.getByText('guide.page_title')).toBeInTheDocument()
  })

  it('renders the page subtitle', () => {
    render(<InteractiveGuide />)
    expect(screen.getByText('guide.page_subtitle')).toBeInTheDocument()
  })

  it('renders a tablist with role tabs label', () => {
    render(<InteractiveGuide />)
    const tablist = screen.getByRole('tablist')
    expect(tablist).toBeInTheDocument()
  })

  it('renders 3 role tabs', () => {
    render(<InteractiveGuide />)
    const tabs = screen.getAllByRole('tab')
    expect(tabs).toHaveLength(3)
  })

  it('shows teacher tab as active by default', () => {
    render(<InteractiveGuide />)
    const teacherTab = screen.getByRole('tab', { name: /guide\.roles\.teacher/i })
    expect(teacherTab).toHaveAttribute('aria-selected', 'true')
  })

  it('renders teacher panel content by default', () => {
    render(<InteractiveGuide />)
    const teacherPanel = screen.getByRole('tabpanel')
    expect(teacherPanel).not.toHaveAttribute('hidden')
    expect(screen.getByText('guide.teacher.heading')).toBeInTheDocument()
  })

  it('switches to student tab on click', async () => {
    render(<InteractiveGuide />)
    const studentTab = screen.getByRole('tab', { name: /guide\.roles\.student/i })
    await user.click(studentTab)

    expect(studentTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('guide.student.heading')).toBeInTheDocument()
  })

  it('switches to parent tab on click', async () => {
    render(<InteractiveGuide />)
    const parentTab = screen.getByRole('tab', { name: /guide\.roles\.parent/i })
    await user.click(parentTab)

    expect(parentTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('guide.parent.heading')).toBeInTheDocument()
  })

  it('inactive tabs have tabIndex -1', () => {
    render(<InteractiveGuide />)
    const studentTab = screen.getByRole('tab', { name: /guide\.roles\.student/i })
    const parentTab = screen.getByRole('tab', { name: /guide\.roles\.parent/i })
    expect(studentTab).toHaveAttribute('tabindex', '-1')
    expect(parentTab).toHaveAttribute('tabindex', '-1')
  })

  it('active tab has tabIndex 0', () => {
    render(<InteractiveGuide />)
    const teacherTab = screen.getByRole('tab', { name: /guide\.roles\.teacher/i })
    expect(teacherTab).toHaveAttribute('tabindex', '0')
  })

  it('has proper ARIA controls on tabs', () => {
    render(<InteractiveGuide />)
    const teacherTab = screen.getByRole('tab', { name: /guide\.roles\.teacher/i })
    expect(teacherTab).toHaveAttribute('aria-controls', 'guide-panel-teacher')
  })

  it('supports keyboard navigation with ArrowRight', async () => {
    render(<InteractiveGuide />)
    const teacherTab = screen.getByRole('tab', { name: /guide\.roles\.teacher/i })
    teacherTab.focus()
    await user.keyboard('{ArrowRight}')

    const studentTab = screen.getByRole('tab', { name: /guide\.roles\.student/i })
    expect(studentTab).toHaveAttribute('aria-selected', 'true')
  })

  it('supports keyboard navigation with ArrowLeft (wraps around)', async () => {
    render(<InteractiveGuide />)
    const teacherTab = screen.getByRole('tab', { name: /guide\.roles\.teacher/i })
    teacherTab.focus()
    await user.keyboard('{ArrowLeft}')

    const parentTab = screen.getByRole('tab', { name: /guide\.roles\.parent/i })
    expect(parentTab).toHaveAttribute('aria-selected', 'true')
  })

  it('renders accordion items inside teacher panel', () => {
    render(<InteractiveGuide />)
    // Teacher has 7 items
    const buttons = screen.getAllByRole('button')
    // Filter out the tab buttons (3 tabs) — remaining are accordion triggers
    const accordionButtons = buttons.filter(
      (b) => b.getAttribute('aria-expanded') !== null,
    )
    expect(accordionButtons).toHaveLength(7)
  })

  it('expands an accordion item on click', async () => {
    render(<InteractiveGuide />)
    const firstAccordion = screen.getAllByRole('button').find(
      (b) => b.getAttribute('aria-expanded') === 'false',
    )!
    expect(firstAccordion).toHaveAttribute('aria-expanded', 'false')

    await user.click(firstAccordion)
    expect(firstAccordion).toHaveAttribute('aria-expanded', 'true')
  })

  it('collapses an expanded accordion item on second click', async () => {
    render(<InteractiveGuide />)
    const firstAccordion = screen.getAllByRole('button').find(
      (b) => b.getAttribute('aria-expanded') === 'false',
    )!

    await user.click(firstAccordion)
    expect(firstAccordion).toHaveAttribute('aria-expanded', 'true')

    await user.click(firstAccordion)
    expect(firstAccordion).toHaveAttribute('aria-expanded', 'false')
  })

  it('renders student panel with 4 accordion items', async () => {
    render(<InteractiveGuide />)
    const studentTab = screen.getByRole('tab', { name: /guide\.roles\.student/i })
    await user.click(studentTab)

    const accordionButtons = screen.getAllByRole('button').filter(
      (b) => b.getAttribute('aria-expanded') !== null,
    )
    expect(accordionButtons).toHaveLength(4)
  })

  it('renders parent panel with 4 accordion items', async () => {
    render(<InteractiveGuide />)
    const parentTab = screen.getByRole('tab', { name: /guide\.roles\.parent/i })
    await user.click(parentTab)

    const accordionButtons = screen.getAllByRole('button').filter(
      (b) => b.getAttribute('aria-expanded') !== null,
    )
    expect(accordionButtons).toHaveLength(4)
  })

  it('has a section landmark with accessible name', () => {
    render(<InteractiveGuide />)
    const section = screen.getByRole('region', { name: 'guide.page_title' })
    expect(section).toBeInTheDocument()
  })
})
