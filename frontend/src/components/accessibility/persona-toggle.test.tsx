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

// Mock accessibility data -- label/description are now i18n keys
vi.mock('@/lib/accessibility-data', () => ({
  PERSONA_LIST: [
    { id: 'standard', label: 'standard', icon: 'U', theme: 'standard', description: 'standard_desc' },
    { id: 'tea', label: 'tea', icon: 'T', theme: 'tea', description: 'tea_desc' },
    { id: 'dyslexia', label: 'dyslexia', icon: 'D', theme: 'dyslexia', description: 'dyslexia_desc' },
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
    expect(group).toHaveAttribute('aria-label', 'personas.select_label')
  })

  it('renders all personas as radio buttons', () => {
    render(<PersonaToggle />)
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(3)
  })

  it('marks the active persona as checked', () => {
    render(<PersonaToggle />)
    const standardRadio = screen.getByRole('radio', { name: /personas\.standard/ })
    expect(standardRadio).toHaveAttribute('aria-checked', 'true')

    const teaRadio = screen.getByRole('radio', { name: /personas\.tea/ })
    expect(teaRadio).toHaveAttribute('aria-checked', 'false')
  })

  it('calls switchTheme when a persona is clicked', async () => {
    render(<PersonaToggle />)
    const teaRadio = screen.getByRole('radio', { name: /personas\.tea/ })
    await user.click(teaRadio)
    expect(mockSwitchTheme).toHaveBeenCalledWith('tea')
  })

  it('calls switchTheme on Enter key press', async () => {
    render(<PersonaToggle />)
    const dyslexiaRadio = screen.getByRole('radio', { name: /personas\.dyslexia/ })
    dyslexiaRadio.focus()
    await user.keyboard('{Enter}')
    expect(mockSwitchTheme).toHaveBeenCalledWith('dyslexia')
  })

  it('calls switchTheme on Space key press', async () => {
    render(<PersonaToggle />)
    const dyslexiaRadio = screen.getByRole('radio', { name: /personas\.dyslexia/ })
    dyslexiaRadio.focus()
    await user.keyboard(' ')
    expect(mockSwitchTheme).toHaveBeenCalledWith('dyslexia')
  })

  it('shows translated persona labels and icons', () => {
    render(<PersonaToggle />)
    // In test mode, useTranslations returns the namespaced key
    expect(screen.getByText('personas.standard')).toBeInTheDocument()
    expect(screen.getByText('personas.tea')).toBeInTheDocument()
    expect(screen.getByText('personas.dyslexia')).toBeInTheDocument()
  })

  it('displays active persona with different styling', () => {
    mockActivePersona = 'tea'
    render(<PersonaToggle />)

    const teaRadio = screen.getByRole('radio', { name: /personas\.tea/ })
    expect(teaRadio).toHaveAttribute('aria-checked', 'true')
    expect(teaRadio).toHaveClass('text-[var(--color-on-primary)]')
  })
})
