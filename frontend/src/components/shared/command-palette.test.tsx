import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CommandPalette, CommandPaletteTrigger } from './command-palette'

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({
      children,
      ...rest
    }: Record<string, unknown> & { children?: React.ReactNode }) => {
      const {
        initial: _i,
        animate: _a,
        exit: _e,
        transition: _t,
        ...safe
      } = rest
      return <div {...safe}>{children}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}))

// Mock accessibility store
vi.mock('@/stores/accessibility-store', () => ({
  useAccessibilityStore: () => ({
    setTheme: vi.fn(),
  }),
}))

function openPalette() {
  fireEvent.keyDown(document, { key: 'k', ctrlKey: true })
}

describe('CommandPalette', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not render dialog initially', () => {
    render(<CommandPalette />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens on Ctrl+K', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('opens on Meta+K (Cmd+K)', () => {
    render(<CommandPalette />)
    fireEvent.keyDown(document, { key: 'k', metaKey: true })
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('closes on Escape', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    fireEvent.keyDown(screen.getByRole('combobox'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('closes on backdrop click', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    const backdrop = screen.getByTestId('command-palette').querySelector('[aria-hidden="true"]')
    if (backdrop) fireEvent.click(backdrop)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows navigation items', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByText('commandPalette.navigation')).toBeInTheDocument()
  })

  it('shows quick actions', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByText('commandPalette.quickActions')).toBeInTheDocument()
  })

  it('shows accessibility theme options', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByText('commandPalette.accessibility')).toBeInTheDocument()
  })

  it('shows language options', () => {
    render(<CommandPalette />)
    openPalette()
    expect(screen.getByText('commandPalette.language')).toBeInTheDocument()
  })

  it('filters results on typing', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'nav.dashboard' } })

    expect(screen.getByText('nav.dashboard')).toBeInTheDocument()
  })

  it('shows no results message for non-matching query', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'xyznonexistent123' } })

    expect(screen.getByText('commandPalette.noResults')).toBeInTheDocument()
  })

  it('navigates with arrow keys', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')

    // First item should be active by default
    expect(input.getAttribute('aria-activedescendant')).toBe('cmd-item-nav-dashboard')

    // Press ArrowDown to move to next item
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    expect(input.getAttribute('aria-activedescendant')).toBe('cmd-item-nav-plans')

    // Press ArrowUp to go back
    fireEvent.keyDown(input, { key: 'ArrowUp' })
    expect(input.getAttribute('aria-activedescendant')).toBe('cmd-item-nav-dashboard')
  })

  it('has proper ARIA attributes on combobox', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')
    expect(input).toHaveAttribute('aria-expanded', 'true')
    expect(input).toHaveAttribute('aria-controls', 'cmd-listbox')
    expect(input).toHaveAttribute('aria-autocomplete', 'list')
  })

  it('has proper ARIA attributes on listbox', () => {
    render(<CommandPalette />)
    openPalette()

    const listbox = screen.getByRole('listbox')
    expect(listbox).toBeInTheDocument()
  })

  it('has option roles on items', () => {
    render(<CommandPalette />)
    openPalette()

    const options = screen.getAllByRole('option')
    expect(options.length).toBeGreaterThan(0)
  })

  it('selects item with Enter and closes dialog', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')
    fireEvent.keyDown(input, { key: 'Enter' })

    // After Enter on a nav item, dialog should close
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('toggles open/close on repeated Ctrl+K', () => {
    render(<CommandPalette />)

    openPalette()
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'k', ctrlKey: true })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('wraps around when navigating past last item', () => {
    render(<CommandPalette />)
    openPalette()

    const input = screen.getByRole('combobox')

    // Filter to a small set
    fireEvent.change(input, { target: { value: 'English' } })

    // Should have the English item active
    expect(input.getAttribute('aria-activedescendant')).toBe('cmd-item-lang-en')

    // ArrowDown wraps to same item (only 1 result)
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    expect(input.getAttribute('aria-activedescendant')).toBe('cmd-item-lang-en')
  })

  it('first option is aria-selected', () => {
    render(<CommandPalette />)
    openPalette()

    const firstOption = screen.getByRole('option', { name: 'nav.dashboard' })
    expect(firstOption).toHaveAttribute('aria-selected', 'true')
  })
})

describe('CommandPaletteTrigger', () => {
  it('renders trigger button with search label', () => {
    render(<CommandPaletteTrigger />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'commandPalette.placeholder')
  })

  it('trigger button can be clicked without error', () => {
    render(<CommandPaletteTrigger />)
    // Trigger button uses a module-level toggle (no synthetic KeyboardEvent)
    expect(() => fireEvent.click(screen.getByRole('button'))).not.toThrow()
  })
})
