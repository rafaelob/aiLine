import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PersonaToggle } from './persona-toggle'

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    span: ({ children, layoutId: _l, initial: _i, animate: _a, transition: _t, ...rest }: Record<string, unknown>) => {
      return <span {...rest}>{children as React.ReactNode}</span>
    },
  },
}))

// Mock useTheme
const mockSwitchTheme = vi.fn()
let mockActivePersona = 'standard'

vi.mock('@/hooks/use-theme', () => ({
  useTheme: () => ({
    activePersona: mockActivePersona,
    switchTheme: mockSwitchTheme,
    resetTheme: vi.fn(),
  }),
}))

// Mock accessibility data
vi.mock('@/lib/accessibility-data', () => ({
  PERSONA_LIST: [
    { id: 'standard', label: 'Padrao', icon: 'U', theme: 'standard', description: 'Padrao' },
    { id: 'tea', label: 'TEA', icon: 'T', theme: 'tea', description: 'Autismo' },
    { id: 'dyslexia', label: 'Dislexia', icon: 'D', theme: 'dyslexia', description: 'Dislexia' },
  ],
}))

describe('PersonaToggle', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockActivePersona = 'standard'
  })

  it('renders a radiogroup with correct ARIA label', () => {
    render(<PersonaToggle />)
    const group = screen.getByRole('radiogroup')
    expect(group).toHaveAttribute('aria-label', 'Selecionar persona de acessibilidade')
  })

  it('renders all personas as radio buttons', () => {
    render(<PersonaToggle />)
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(3)
  })

  it('marks the active persona as checked', () => {
    render(<PersonaToggle />)
    const standardRadio = screen.getByRole('radio', { name: /Padrao/ })
    expect(standardRadio).toHaveAttribute('aria-checked', 'true')

    const teaRadio = screen.getByRole('radio', { name: /TEA/ })
    expect(teaRadio).toHaveAttribute('aria-checked', 'false')
  })

  it('calls switchTheme when a persona is clicked', async () => {
    render(<PersonaToggle />)
    const teaRadio = screen.getByRole('radio', { name: /TEA/ })
    await user.click(teaRadio)
    expect(mockSwitchTheme).toHaveBeenCalledWith('tea')
  })

  it('calls switchTheme on Enter key press', async () => {
    render(<PersonaToggle />)
    const dyslexiaRadio = screen.getByRole('radio', { name: /Dislexia/ })
    dyslexiaRadio.focus()
    await user.keyboard('{Enter}')
    expect(mockSwitchTheme).toHaveBeenCalledWith('dyslexia')
  })

  it('calls switchTheme on Space key press', async () => {
    render(<PersonaToggle />)
    const dyslexiaRadio = screen.getByRole('radio', { name: /Dislexia/ })
    dyslexiaRadio.focus()
    await user.keyboard(' ')
    expect(mockSwitchTheme).toHaveBeenCalledWith('dyslexia')
  })

  it('shows persona labels and icons', () => {
    render(<PersonaToggle />)
    expect(screen.getByText('Padrao')).toBeInTheDocument()
    expect(screen.getByText('TEA')).toBeInTheDocument()
    expect(screen.getByText('Dislexia')).toBeInTheDocument()
  })

  it('displays active persona with different styling', () => {
    mockActivePersona = 'tea'
    render(<PersonaToggle />)

    const teaRadio = screen.getByRole('radio', { name: /TEA/ })
    expect(teaRadio).toHaveAttribute('aria-checked', 'true')
    expect(teaRadio).toHaveClass('text-[var(--color-on-primary)]')
  })
})
