import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import AccessibilityPage from './page'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, layoutId: _l, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('@/hooks/use-theme', () => ({
  useTheme: () => ({
    activePersona: 'standard',
    switchTheme: vi.fn(),
    resetTheme: vi.fn(),
  }),
}))

vi.mock('@/hooks/use-dyslexia-simulator', () => ({
  useDyslexiaSimulator: () => ({
    startSimulation: vi.fn(),
    stopSimulation: vi.fn(),
    targetRef: { current: null },
  }),
}))

vi.mock('@/lib/accessibility-data', async (importOriginal) => {
  const actual = await importOriginal() as Record<string, unknown>
  return {
    ...actual,
    PERSONA_LIST: [
      { id: 'standard', label: 'Padrao', icon: 'U', theme: 'standard', description: 'Padrao' },
    ],
  }
})

describe('AccessibilityPage', () => {
  it('renders the page heading', () => {
    render(<AccessibilityPage />)
    expect(screen.getByText('Acessibilidade')).toBeInTheDocument()
  })

  it('renders the description text', () => {
    render(<AccessibilityPage />)
    expect(screen.getByText(/Personalize a experiência/i)).toBeInTheDocument()
  })

  it('renders the Persona section heading', () => {
    render(<AccessibilityPage />)
    expect(screen.getByText('Persona de Acessibilidade')).toBeInTheDocument()
  })

  it('renders the Accessibility Twin section heading', () => {
    render(<AccessibilityPage />)
    expect(screen.getByText('Comparação de Versões')).toBeInTheDocument()
  })

  it('renders the Simulate Disability section', () => {
    render(<AccessibilityPage />)
    expect(screen.getByText('Ponte de Empatia')).toBeInTheDocument()
  })

  it('renders the color blind filters SVG', () => {
    const { container } = render(<AccessibilityPage />)
    const svg = container.querySelector('svg[aria-hidden="true"]')
    expect(svg).toBeInTheDocument()
  })

  it('renders as a main landmark', () => {
    render(<AccessibilityPage />)
    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
  })
})
