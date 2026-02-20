import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginFormPhase } from './login-form-phase'
import type { DemoProfile } from './login-data'

vi.mock('./login-data', () => ({
  ROLES: [
    { id: 'teacher', icon: 'M12 0', color: 'from-blue-500 to-blue-600', badge: 'start_here' },
    { id: 'student', icon: 'M12 0', color: 'from-green-500 to-green-600', badge: null },
  ],
}))

const DEMO_PROFILE: DemoProfile = {
  key: 'teacher',
  name: 'Ms. Sarah Johnson',
  avatar: 'SJ',
  description: 'demo_teacher_desc',
  color: 'from-blue-500 to-indigo-600',
  route: '/dashboard',
}

describe('LoginFormPhase', () => {
  const user = userEvent.setup()
  const defaultProps = {
    locale: 'en',
    noMotion: true,
    selectedRole: 'teacher' as const,
    demoProfiles: [DEMO_PROFILE],
    email: '',
    password: '',
    isLoading: false,
    error: null,
    onBack: vi.fn(),
    onDemoLogin: vi.fn(),
    onEmailChange: vi.fn(),
    onPasswordChange: vi.fn(),
    onSubmit: vi.fn(),
  }

  it('renders the back button with aria-label', () => {
    render(<LoginFormPhase {...defaultProps} />)
    expect(screen.getByLabelText('login.back_to_roles')).toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', async () => {
    const onBack = vi.fn()
    render(<LoginFormPhase {...defaultProps} onBack={onBack} />)
    await user.click(screen.getByLabelText('login.back_to_roles'))
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('renders role heading and description', () => {
    render(<LoginFormPhase {...defaultProps} />)
    expect(screen.getByText('login.role_teacher')).toBeInTheDocument()
    expect(screen.getByText('login.role_teacher_desc')).toBeInTheDocument()
  })

  it('renders demo profiles section when profiles are provided', () => {
    render(<LoginFormPhase {...defaultProps} />)
    expect(screen.getByText('login.demo_section_title')).toBeInTheDocument()
    expect(screen.getByText('Ms. Sarah Johnson')).toBeInTheDocument()
  })

  it('hides demo profiles section when list is empty', () => {
    render(<LoginFormPhase {...defaultProps} demoProfiles={[]} />)
    expect(screen.queryByText('login.demo_section_title')).not.toBeInTheDocument()
  })

  it('calls onDemoLogin when a demo profile is clicked', async () => {
    const onDemoLogin = vi.fn()
    render(<LoginFormPhase {...defaultProps} onDemoLogin={onDemoLogin} />)
    await user.click(screen.getByLabelText('landing.demo_enter_as Ms. Sarah Johnson'))
    expect(onDemoLogin).toHaveBeenCalledWith(DEMO_PROFILE)
  })

  it('renders email and password inputs', () => {
    render(<LoginFormPhase {...defaultProps} />)
    expect(screen.getByLabelText('login.email_label')).toBeInTheDocument()
    expect(screen.getByLabelText('login.password_label')).toBeInTheDocument()
  })

  it('calls onEmailChange and onPasswordChange on input', async () => {
    const onEmailChange = vi.fn()
    const onPasswordChange = vi.fn()
    render(
      <LoginFormPhase
        {...defaultProps}
        onEmailChange={onEmailChange}
        onPasswordChange={onPasswordChange}
      />,
    )
    await user.type(screen.getByLabelText('login.email_label'), 'a')
    expect(onEmailChange).toHaveBeenCalledWith('a')

    await user.type(screen.getByLabelText('login.password_label'), 'x')
    expect(onPasswordChange).toHaveBeenCalledWith('x')
  })

  it('disables submit when email or password is empty', () => {
    render(<LoginFormPhase {...defaultProps} email="" password="" />)
    const btn = screen.getByRole('button', { name: 'login.sign_in' })
    expect(btn).toBeDisabled()
  })

  it('disables submit when isLoading is true', () => {
    render(<LoginFormPhase {...defaultProps} email="a@b.c" password="pwd" isLoading />)
    // When loading, text changes to 'signing_in'
    const btn = screen.getByText('login.signing_in').closest('button')!
    expect(btn).toBeDisabled()
  })

  it('enables submit when email and password are set', () => {
    render(<LoginFormPhase {...defaultProps} email="test@example.com" password="pass123" />)
    const btn = screen.getByRole('button', { name: 'login.sign_in' })
    expect(btn).not.toBeDisabled()
  })

  it('displays error message with alert role', () => {
    render(<LoginFormPhase {...defaultProps} error="Invalid credentials" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Invalid credentials')
  })

  it('does not display error when error is null', () => {
    render(<LoginFormPhase {...defaultProps} error={null} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders or_sign_in divider text', () => {
    render(<LoginFormPhase {...defaultProps} />)
    expect(screen.getByText('login.or_sign_in')).toBeInTheDocument()
  })

  it('renders back-to-home link', () => {
    render(<LoginFormPhase {...defaultProps} locale="pt-BR" />)
    const link = screen.getByText('login.back_to_home')
    expect(link.closest('a')).toHaveAttribute('href', '/pt-BR/')
  })

  it('shows loading spinner text when isLoading', () => {
    render(<LoginFormPhase {...defaultProps} email="a@b.c" password="p" isLoading />)
    expect(screen.getByText('login.signing_in')).toBeInTheDocument()
    expect(screen.queryByText('login.sign_in')).not.toBeInTheDocument()
  })

  it('calls onSubmit when form is submitted', async () => {
    const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault())
    render(
      <LoginFormPhase
        {...defaultProps}
        email="test@example.com"
        password="pass123"
        onSubmit={onSubmit}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'login.sign_in' }))
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })
})
