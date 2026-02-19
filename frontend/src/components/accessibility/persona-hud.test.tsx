import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PersonaHUD } from './persona-hud'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockSwitchTheme = vi.fn((id: string) => {
  document.body.setAttribute('data-theme', id)
})

vi.mock('@/hooks/use-theme', () => ({
  useTheme: () => ({
    activePersona: 'standard',
    switchTheme: mockSwitchTheme,
    resetTheme: vi.fn(),
  }),
}))

describe('PersonaHUD', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.setAttribute('data-theme', 'standard')
  })

  it('renders as a nav with accessible label', () => {
    render(<PersonaHUD />)
    const nav = screen.getByRole('navigation', { name: 'accessibility.hud_label' })
    expect(nav).toBeInTheDocument()
  })

  it('renders 3 hero persona buttons', () => {
    render(<PersonaHUD />)
    // The hero buttons use hero_* translation keys
    const buttons = screen.getAllByRole('radio')
    // 3 hero buttons
    expect(buttons.length).toBe(3)
  })

  it('renders expand toggle button', () => {
    render(<PersonaHUD />)
    const expandBtn = screen.getByRole('button', { name: 'accessibility.all_personas' })
    expect(expandBtn).toBeInTheDocument()
    expect(expandBtn).toHaveAttribute('aria-expanded', 'false')
  })

  it('expands to show all 9 personas when expand is clicked', () => {
    render(<PersonaHUD />)
    const expandBtn = screen.getByRole('button', { name: 'accessibility.all_personas' })

    fireEvent.click(expandBtn)

    expect(expandBtn).toHaveAttribute('aria-expanded', 'true')
    // Now there should be 3 hero + 9 expanded = 12 radio buttons
    const allRadios = screen.getAllByRole('radio')
    expect(allRadios.length).toBe(12)
  })

  it('collapses the expanded panel when toggled again', () => {
    render(<PersonaHUD />)
    const expandBtn = screen.getByRole('button', { name: 'accessibility.all_personas' })

    fireEvent.click(expandBtn) // expand
    fireEvent.click(expandBtn) // collapse

    expect(expandBtn).toHaveAttribute('aria-expanded', 'false')
    // Back to 3 hero buttons only
    const radios = screen.getAllByRole('radio')
    expect(radios.length).toBe(3)
  })

  it('calls switchTheme when a persona is clicked', () => {
    render(<PersonaHUD />)
    const dyslexiaBtn = screen.getByRole('radio', { name: 'accessibility.themes.dyslexia' })

    fireEvent.click(dyslexiaBtn)

    expect(mockSwitchTheme).toHaveBeenCalledWith('dyslexia')
  })

  it('shows toast notification after switching persona', () => {
    render(<PersonaHUD />)
    const dyslexiaBtn = screen.getByRole('radio', { name: 'accessibility.themes.dyslexia' })

    fireEvent.click(dyslexiaBtn)

    const toast = screen.getByRole('status')
    expect(toast).toBeInTheDocument()
  })

  it('sets data-theme on document.body when switching', () => {
    render(<PersonaHUD />)
    const dyslexiaBtn = screen.getByRole('radio', { name: 'accessibility.themes.dyslexia' })

    fireEvent.click(dyslexiaBtn)

    expect(document.body.getAttribute('data-theme')).toBe('dyslexia')
  })

  it('marks active persona with aria-checked', () => {
    render(<PersonaHUD />)
    // Standard is active, so none of the hero buttons should be checked
    const radios = screen.getAllByRole('radio')
    radios.forEach((radio) => {
      // None of the hero buttons (low_vision, dyslexia, tdah) match 'standard'
      expect(radio).toHaveAttribute('aria-checked', 'false')
    })
  })

  it('has radiogroup role on expanded panel', () => {
    render(<PersonaHUD />)
    const expandBtn = screen.getByRole('button', { name: 'accessibility.all_personas' })
    fireEvent.click(expandBtn)

    const radioGroup = screen.getByRole('radiogroup', { name: 'accessibility.all_personas' })
    expect(radioGroup).toBeInTheDocument()
  })
})
