import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { GestureList } from './gesture-list'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

const mockGestures = {
  gestures: [
    { id: 'oi', name_pt: 'Ola', name_en: 'Hello', name_es: 'Hola' },
    { id: 'obrigado', name_pt: 'Obrigado', name_en: 'Thank you', name_es: 'Gracias' },
    { id: 'sim', name_pt: 'Sim', name_en: 'Yes', name_es: 'Si' },
    { id: 'nao', name_pt: 'Nao', name_en: 'No', name_es: 'No' },
  ],
  model: 'mlp-v1',
  note: 'MVP gestures',
}

describe('GestureList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {})) // Never resolves
    render(<GestureList />)
    expect(screen.getByText('sign_language.loading_gestures')).toBeInTheDocument()
  })

  it('renders gesture cards after successful fetch', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGestures,
    })

    render(<GestureList />)

    // Locale from mock is pt-BR, so use Portuguese names
    await waitFor(() => {
      expect(screen.getByText('Ola')).toBeInTheDocument()
    })
    expect(screen.getByText('Obrigado')).toBeInTheDocument()
    expect(screen.getByText('Sim')).toBeInTheDocument()
    expect(screen.getByText('Nao')).toBeInTheDocument()
  })

  it('shows gesture IDs', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGestures,
    })

    render(<GestureList />)

    await waitFor(() => {
      expect(screen.getByText('oi')).toBeInTheDocument()
    })
    expect(screen.getByText('obrigado')).toBeInTheDocument()
  })

  it('shows error state on fetch failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    render(<GestureList />)

    await waitFor(() => {
      expect(
        screen.getByText('sign_language.error_loading_gestures')
      ).toBeInTheDocument()
    })
  })

  it('shows error on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    })

    render(<GestureList />)

    await waitFor(() => {
      expect(
        screen.getByText('sign_language.error_loading_gestures')
      ).toBeInTheDocument()
    })
  })

  it('renders heading after load', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGestures,
    })

    render(<GestureList />)

    await waitFor(() => {
      expect(
        screen.getByText('sign_language.supported_gestures')
      ).toBeInTheDocument()
    })
  })

  it('renders gesture note text', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGestures,
    })

    render(<GestureList />)

    await waitFor(() => {
      expect(screen.getByText('sign_language.gestures_note')).toBeInTheDocument()
    })
  })

  it('applies custom className', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGestures,
    })

    const { container } = render(<GestureList className="my-class" />)

    await waitFor(() => {
      expect(container.firstElementChild).toHaveClass('my-class')
    })
  })

  it('renders error with alert role', async () => {
    mockFetch.mockRejectedValueOnce(new Error('fail'))

    render(<GestureList />)

    await waitFor(() => {
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
    })
  })
})
