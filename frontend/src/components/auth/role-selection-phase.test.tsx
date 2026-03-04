import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RoleSelectionPhase } from './role-selection-phase'

vi.mock('./login-data', () => ({
  ROLES: [
    { id: 'teacher', icon: 'M12 14l9-5-9-5-9 5 9 5z', color: 'from-blue-500 to-blue-600', badge: null },
    { id: 'student', icon: 'M12 14l9-5-9-5-9 5 9 5z', color: 'from-green-500 to-green-600', badge: null },
    { id: 'parent', icon: 'M12 14l9-5-9-5-9 5 9 5z', color: 'from-amber-500 to-amber-600', badge: null },
  ],
}))

describe('RoleSelectionPhase', () => {
  const user = userEvent.setup()
  const defaultProps = {
    locale: 'en',
    noMotion: true,
    onRoleSelect: vi.fn(),
  }

  it('renders the role selection heading', () => {
    render(<RoleSelectionPhase {...defaultProps} />)
    expect(screen.getByText('login.choose_role')).toBeInTheDocument()
  })

  it('renders a button for each role', () => {
    render(<RoleSelectionPhase {...defaultProps} />)
    expect(screen.getByLabelText('login.role_teacher')).toBeInTheDocument()
    expect(screen.getByLabelText('login.role_student')).toBeInTheDocument()
    expect(screen.getByLabelText('login.role_parent')).toBeInTheDocument()
  })

  it('renders role names and descriptions', () => {
    render(<RoleSelectionPhase {...defaultProps} />)
    expect(screen.getByText('login.role_teacher')).toBeInTheDocument()
    expect(screen.getByText('login.role_teacher_desc')).toBeInTheDocument()
    expect(screen.getByText('login.role_student')).toBeInTheDocument()
    expect(screen.getByText('login.role_student_desc')).toBeInTheDocument()
  })

  it('calls onRoleSelect with the correct role when clicked', async () => {
    const onRoleSelect = vi.fn()
    render(<RoleSelectionPhase {...defaultProps} onRoleSelect={onRoleSelect} />)

    await user.click(screen.getByLabelText('login.role_teacher'))
    expect(onRoleSelect).toHaveBeenCalledWith('teacher')

    await user.click(screen.getByLabelText('login.role_student'))
    expect(onRoleSelect).toHaveBeenCalledWith('student')
  })

  it('renders a group with accessible label', () => {
    render(<RoleSelectionPhase {...defaultProps} />)
    const group = screen.getByRole('group')
    expect(group).toHaveAttribute('aria-label', 'login.choose_role')
  })

  it('renders back-to-home link with correct locale', () => {
    render(<RoleSelectionPhase {...defaultProps} locale="pt-BR" />)
    const link = screen.getByText('login.back_to_home')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/pt-BR')
  })

  it('renders buttons that are focusable', () => {
    render(<RoleSelectionPhase {...defaultProps} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(3)
    for (const button of buttons) {
      expect(button).not.toHaveAttribute('disabled')
    }
  })
})
