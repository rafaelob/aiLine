import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ClassroomMode } from './classroom-mode'

describe('ClassroomMode', () => {
  const user = userEvent.setup()

  it('renders with accessible section label', () => {
    render(<ClassroomMode />)
    const section = document.querySelector('section')
    expect(section).toHaveAttribute('aria-label', 'classroom.title')
  })

  it('renders the subtitle heading', () => {
    render(<ClassroomMode />)
    expect(screen.getByText('classroom.subtitle')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(<ClassroomMode />)
    expect(screen.getByText('classroom.description')).toBeInTheDocument()
  })

  it('renders 4 student cards', () => {
    render(<ClassroomMode />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(4)
  })

  it('renders each student name', () => {
    render(<ClassroomMode />)
    expect(screen.getByText('classroom.student_lucas')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_sofia')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_pedro')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_ana')).toBeInTheDocument()
  })

  it('renders each student profile badge', () => {
    render(<ClassroomMode />)
    expect(screen.getByText('classroom.student_lucas_profile')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_sofia_profile')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_pedro_profile')).toBeInTheDocument()
    expect(screen.getByText('classroom.student_ana_profile')).toBeInTheDocument()
  })

  it('renders adaptation sections', () => {
    render(<ClassroomMode />)
    const adaptations = screen.getAllByText('classroom.card_adaptation')
    expect(adaptations).toHaveLength(4)
  })

  it('renders accommodation badges for each student', () => {
    render(<ClassroomMode />)
    // Lucas badges
    expect(screen.getByText('classroom.badge_visual_schedule')).toBeInTheDocument()
    expect(screen.getByText('classroom.badge_calm_colors')).toBeInTheDocument()
    // Sofia badges
    expect(screen.getByText('classroom.badge_timer')).toBeInTheDocument()
    expect(screen.getByText('classroom.badge_focus_mode')).toBeInTheDocument()
    // Pedro badges
    expect(screen.getByText('classroom.badge_bionic_reading')).toBeInTheDocument()
    expect(screen.getByText('classroom.badge_warm_tones')).toBeInTheDocument()
    // Ana badges
    expect(screen.getByText('classroom.badge_sign_language')).toBeInTheDocument()
    expect(screen.getByText('classroom.badge_captions')).toBeInTheDocument()
  })

  it('has plan preview buttons with aria-expanded', () => {
    render(<ClassroomMode />)
    const snippetButtons = screen.getAllByRole('button', { expanded: false })
    expect(snippetButtons.length).toBeGreaterThanOrEqual(4)
  })

  it('expands plan snippet on click', async () => {
    render(<ClassroomMode />)
    // All snippet buttons have aria-expanded="false"
    const expandButtons = screen.getAllByRole('button', { expanded: false })
    expect(expandButtons.length).toBeGreaterThanOrEqual(1)

    await user.click(expandButtons[0])

    // After click, check that at least one button is now expanded
    const expandedButtons = screen.queryAllByRole('button', { expanded: true })
    expect(expandedButtons.length).toBe(1)
  })

  it('collapses snippet when clicking again', async () => {
    render(<ClassroomMode />)
    const expandButtons = screen.getAllByRole('button', { expanded: false })

    // Expand first
    await user.click(expandButtons[0])
    expect(screen.queryAllByRole('button', { expanded: true })).toHaveLength(1)

    // Collapse by clicking the expanded button
    const expandedBtn = screen.getByRole('button', { expanded: true })
    await user.click(expandedBtn)

    expect(screen.queryAllByRole('button', { expanded: true })).toHaveLength(0)
  })

  it('has a list role on the grid', () => {
    render(<ClassroomMode />)
    const list = screen.getByRole('list')
    expect(list).toHaveAttribute('aria-label', 'classroom.title')
  })

  it('applies custom className', () => {
    render(<ClassroomMode className="my-test-class" />)
    const section = document.querySelector('section')
    expect(section).toHaveClass('my-test-class')
  })

  it('renders colored accent stripes on each card', () => {
    const { container } = render(<ClassroomMode />)
    const stripes = container.querySelectorAll('[aria-hidden="true"]')
    // Each card has an icon div (aria-hidden) + a stripe div (aria-hidden)
    // so we should have at least 4 stripe divs
    const stripeDivs = Array.from(stripes).filter(
      (el) => el.classList.contains('h-1') && el.classList.contains('w-full'),
    )
    expect(stripeDivs).toHaveLength(4)
  })
})
