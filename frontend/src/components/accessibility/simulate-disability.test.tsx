import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SimulateDisability } from './simulate-disability'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('@/hooks/use-dyslexia-simulator', () => ({
  useDyslexiaSimulator: () => ({
    startSimulation: vi.fn(),
    stopSimulation: vi.fn(),
    targetRef: { current: null },
  }),
}))

describe('SimulateDisability', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    document.documentElement.style.filter = ''
  })

  it('renders the section heading', () => {
    render(<SimulateDisability />)
    expect(screen.getByText('simulate.title')).toBeInTheDocument()
  })

  it('renders simulation categories as fieldsets', () => {
    render(<SimulateDisability />)
    const fieldsets = screen.getAllByRole('group')
    expect(fieldsets.length).toBeGreaterThanOrEqual(4)
  })

  it('renders simulation toggles as switches', () => {
    render(<SimulateDisability />)
    const switches = screen.getAllByRole('switch')
    expect(switches).toHaveLength(7)
  })

  it('all switches are unchecked initially', () => {
    render(<SimulateDisability />)
    const switches = screen.getAllByRole('switch')
    for (const sw of switches) {
      expect(sw).not.toBeChecked()
    }
  })

  it('does not show reset button when no simulations are active', () => {
    render(<SimulateDisability />)
    expect(screen.queryByText('simulate.reset_all')).not.toBeInTheDocument()
  })

  it('toggles a simulation on click', async () => {
    render(<SimulateDisability />)
    const protanopiaSwitch = screen.getByRole('switch', {
      name: /Protanopia/i,
    })

    await user.click(protanopiaSwitch)
    expect(protanopiaSwitch).toBeChecked()
  })

  it('shows reset button when a simulation is active', async () => {
    render(<SimulateDisability />)
    const protanopiaSwitch = screen.getByRole('switch', {
      name: /Protanopia/i,
    })

    await user.click(protanopiaSwitch)
    expect(screen.getByText('simulate.reset_all')).toBeInTheDocument()
  })

  it('shows active simulation count status', async () => {
    render(<SimulateDisability />)
    const protanopiaSwitch = screen.getByRole('switch', {
      name: /Protanopia/i,
    })

    await user.click(protanopiaSwitch)

    const status = screen.getByRole('status')
    expect(status).toHaveTextContent(/simulate\.active_simulations/)
  })

  it('reset button deactivates all simulations', async () => {
    render(<SimulateDisability />)

    const protanopiaSwitch = screen.getByRole('switch', {
      name: /Protanopia/i,
    })
    await user.click(protanopiaSwitch)

    const resetButton = screen.getByText('simulate.reset_all')
    await user.click(resetButton)

    const switches = screen.getAllByRole('switch')
    for (const sw of switches) {
      expect(sw).not.toBeChecked()
    }
  })

  it('displays simulation labels and descriptions', () => {
    render(<SimulateDisability />)
    expect(screen.getByText('Protanopia')).toBeInTheDocument()
    expect(screen.getByText('Deuteranopia')).toBeInTheDocument()
    expect(screen.getByText('Tritanopia')).toBeInTheDocument()
    expect(screen.getByText('Baixa Visão')).toBeInTheDocument()
    expect(screen.getByText(/Dislexia/)).toBeInTheDocument()
  })
})
