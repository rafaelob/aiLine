import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LandingDemoLogin } from './landing-demo-login'

const mockPush = vi.fn()
const mockPrefetch = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, prefetch: mockPrefetch }),
}))

vi.mock('motion/react', () => ({
  motion: {
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  useInView: () => true,
  useReducedMotion: () => false,
}))

const mockSetTheme = vi.fn()
vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ setTheme: mockSetTheme, theme: 'standard' }),
}))

const defaultProps = {
  locale: 'en',
  title: 'Try the Demo',
  subtitle: 'Choose a profile',
  enterAs: 'Enter',
  teacherLabel: 'Teacher',
  studentLabel: 'Student',
  parentLabel: 'Parent',
  profiles: {
    teacher: {
      name: 'Ms. Sarah Johnson',
      detail: '5th Grade Science',
      description: 'Experience creating inclusive lesson plans',
    },
    students: {
      alex: {
        name: 'Alex Rivera',
        condition: 'ASD',
        description: 'See how content adapts for autism',
      },
      maya: {
        name: 'Maya Chen',
        condition: 'ADHD',
        description: 'Experience focus mode',
      },
      lucas: {
        name: 'Lucas Thompson',
        condition: 'Dyslexia',
        description: 'Try bionic reading',
      },
      sofia: {
        name: 'Sofia Martinez',
        condition: 'Hearing',
        description: 'See sign language support',
      },
    },
    parent: {
      name: 'David Rivera',
      description: 'View your child\'s progress',
    },
  },
}

describe('LandingDemoLogin', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    document.body.removeAttribute('data-theme')
  })

  it('renders without crashing', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument()
  })

  it('renders the section title and subtitle', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    expect(screen.getByText('Try the Demo')).toBeInTheDocument()
    expect(screen.getByText('Choose a profile')).toBeInTheDocument()
  })

  it('renders all 6 profile cards', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    expect(screen.getByText('Ms. Sarah Johnson')).toBeInTheDocument()
    expect(screen.getByText('Alex Rivera')).toBeInTheDocument()
    expect(screen.getByText('Maya Chen')).toBeInTheDocument()
    expect(screen.getByText('Lucas Thompson')).toBeInTheDocument()
    expect(screen.getByText('Sofia Martinez')).toBeInTheDocument()
    expect(screen.getByText('David Rivera')).toBeInTheDocument()
  })

  it('renders Enter buttons with aria-labels', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(6)
    expect(buttons[0]).toHaveAttribute('aria-label', 'Enter Ms. Sarah Johnson')
  })

  it('renders accessibility condition badges for students', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    expect(screen.getByText('ASD')).toBeInTheDocument()
    expect(screen.getByText('ADHD')).toBeInTheDocument()
    expect(screen.getByText('Dyslexia')).toBeInTheDocument()
    expect(screen.getByText('Hearing')).toBeInTheDocument()
  })

  it('clicking teacher Enter navigates to dashboard', async () => {
    render(<LandingDemoLogin {...defaultProps} />)
    const teacherBtn = screen.getByRole('button', { name: /enter ms. sarah johnson/i })
    await user.click(teacherBtn)

    expect(mockPush).toHaveBeenCalledWith('/en/dashboard')
    expect(sessionStorage.getItem('ailine_demo_profile')).toBe('teacher-sarah')
    expect(sessionStorage.getItem('ailine_demo_role')).toBe('teacher')
  })

  it('clicking student Enter sets accessibility theme and navigates', async () => {
    render(<LandingDemoLogin {...defaultProps} />)
    const alexBtn = screen.getByRole('button', { name: /enter alex rivera/i })
    await user.click(alexBtn)

    expect(mockSetTheme).toHaveBeenCalledWith('tea')
    expect(document.body.getAttribute('data-theme')).toBe('tea')
    expect(mockPush).toHaveBeenCalledWith('/en/tutors')
    expect(sessionStorage.getItem('ailine_demo_profile')).toBe('student-alex')
  })

  it('clicking parent Enter navigates to progress page', async () => {
    render(<LandingDemoLogin {...defaultProps} />)
    const parentBtn = screen.getByRole('button', { name: /enter david rivera/i })
    await user.click(parentBtn)

    expect(mockPush).toHaveBeenCalledWith('/en/progress')
    expect(sessionStorage.getItem('ailine_demo_role')).toBe('parent')
  })

  it('section has aria-labelledby pointing to heading', () => {
    const { container } = render(<LandingDemoLogin {...defaultProps} />)
    const section = container.querySelector('section')
    expect(section).toHaveAttribute('aria-labelledby', 'demo-login-heading')
  })

  it('renders role labels for each profile', () => {
    render(<LandingDemoLogin {...defaultProps} />)
    const teacherLabels = screen.getAllByText('Teacher')
    expect(teacherLabels.length).toBeGreaterThanOrEqual(1)
    const studentLabels = screen.getAllByText('Student')
    expect(studentLabels.length).toBeGreaterThanOrEqual(1)
    const parentLabels = screen.getAllByText('Parent')
    expect(parentLabels.length).toBeGreaterThanOrEqual(1)
  })
})
