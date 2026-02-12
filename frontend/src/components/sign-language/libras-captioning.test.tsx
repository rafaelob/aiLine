import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LibrasCaptioning } from './libras-captioning'

// Mock motion library
vi.mock('motion/react', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    span: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <span {...safe}>{children as React.ReactNode}</span>
    },
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

// Mock the captioning hook
const mockStartCaptioning = vi.fn()
const mockStopCaptioning = vi.fn()
const mockFeedLandmarks = vi.fn()

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

let mockState: {
  isRecording: boolean
  rawGlosses: string[]
  draftText: string
  committedText: string
  confidence: number
  connectionStatus: ConnectionStatus
  error: string | null
} = {
  isRecording: false,
  rawGlosses: [],
  draftText: '',
  committedText: '',
  confidence: 0,
  connectionStatus: 'disconnected',
  error: null,
}

vi.mock('@/hooks/use-libras-captioning', () => ({
  useLibrasCaptioning: () => ({
    ...mockState,
    startCaptioning: mockStartCaptioning,
    stopCaptioning: mockStopCaptioning,
    feedLandmarks: mockFeedLandmarks,
  }),
}))

describe('LibrasCaptioning', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockState = {
      isRecording: false,
      rawGlosses: [],
      draftText: '',
      committedText: '',
      confidence: 0,
      connectionStatus: 'disconnected',
      error: null,
    }
  })

  it('renders captioning title', () => {
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_title')).toBeInTheDocument()
  })

  it('renders description text', () => {
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_description')).toBeInTheDocument()
  })

  it('shows start button when not recording', () => {
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_start')).toBeInTheDocument()
  })

  it('calls startCaptioning when start button clicked', async () => {
    render(<LibrasCaptioning />)
    await user.click(screen.getByText('sign_language.captioning_start'))
    expect(mockStartCaptioning).toHaveBeenCalledOnce()
  })

  it('shows stop button when recording', () => {
    mockState.isRecording = true
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_stop')).toBeInTheDocument()
  })

  it('calls stopCaptioning when stop button clicked', async () => {
    mockState.isRecording = true
    render(<LibrasCaptioning />)
    await user.click(screen.getByText('sign_language.captioning_stop'))
    expect(mockStopCaptioning).toHaveBeenCalledOnce()
  })

  it('shows connecting state', () => {
    mockState.connectionStatus = 'connecting'
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_connecting')).toBeInTheDocument()
  })

  it('shows no signs message when idle', () => {
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_no_signs')).toBeInTheDocument()
  })

  it('displays raw glosses when available', () => {
    mockState.rawGlosses = ['EU', 'GOSTAR']
    render(<LibrasCaptioning />)
    expect(screen.getByText('EU GOSTAR')).toBeInTheDocument()
  })

  it('displays committed text', () => {
    mockState.committedText = 'Eu gosto da escola.'
    render(<LibrasCaptioning />)
    expect(screen.getByText('Eu gosto da escola.')).toBeInTheDocument()
  })

  it('displays draft text in muted style', () => {
    mockState.draftText = 'Traduzindo...'
    render(<LibrasCaptioning />)
    expect(screen.getByText('Traduzindo...')).toBeInTheDocument()
  })

  it('shows recording indicator when recording', () => {
    mockState.isRecording = true
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_recording')).toBeInTheDocument()
  })

  it('shows confidence bar when recording with confidence', () => {
    mockState.isRecording = true
    mockState.confidence = 0.85
    render(<LibrasCaptioning />)
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows error message when error exists', () => {
    mockState.error = 'Test error'
    render(<LibrasCaptioning />)
    expect(screen.getByText('sign_language.captioning_error')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<LibrasCaptioning className="test-class" />)
    expect(container.firstElementChild).toHaveClass('test-class')
  })

  it('has aria-live on caption display area', () => {
    render(<LibrasCaptioning />)
    const liveRegion = screen.getByText('sign_language.captioning_glosses').closest('[aria-live]')
    expect(liveRegion).toHaveAttribute('aria-live', 'polite')
  })

  it('has aria-pressed on toggle button', () => {
    render(<LibrasCaptioning />)
    const button = screen.getByText('sign_language.captioning_start')
    expect(button).toHaveAttribute('aria-pressed', 'false')
  })
})
