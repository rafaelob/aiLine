import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import WebcamCapture from './webcam-capture'

vi.mock('motion/react', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
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

// Mock the sign language worker hook (Worker not available in jsdom)
vi.mock('@/hooks/use-sign-language-worker', () => ({
  useSignLanguageWorker: () => ({
    ready: false,
    error: null,
    lastResult: null,
    lastLandmarks: null,
    classify: vi.fn(),
    extractLandmarks: vi.fn(),
    setLandmarkListener: vi.fn(),
  }),
}))

// Mock the captioning hook (Worker not available in jsdom)
const mockStartCaptioning = vi.fn()
const mockStopCaptioning = vi.fn()
const mockFeedLandmarks = vi.fn()

vi.mock('@/hooks/use-libras-captioning', () => ({
  useLibrasCaptioning: () => ({
    isRecording: false,
    rawGlosses: [],
    draftText: '',
    committedText: '',
    confidence: 0,
    connectionStatus: 'disconnected' as const,
    error: null,
    startCaptioning: mockStartCaptioning,
    stopCaptioning: mockStopCaptioning,
    feedLandmarks: mockFeedLandmarks,
  }),
}))

const mockGetUserMedia = vi.fn()
const mockTrackStop = vi.fn()

describe('WebcamCapture', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock getUserMedia
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      writable: true,
      configurable: true,
    })

    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: mockTrackStop }],
    })
  })

  it('renders webcam heading', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.webcam')).toBeInTheDocument()
  })

  it('shows start camera button initially', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.start_camera')).toBeInTheDocument()
  })

  it('shows webcam off message initially', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.webcam_off')).toBeInTheDocument()
  })

  it('calls getUserMedia when start camera is clicked', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
  })

  it('shows captioning and stop buttons after starting camera', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(screen.getByText('sign_language.continuous_start')).toBeInTheDocument()
    expect(screen.getByText('sign_language.stop_camera')).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_allowed error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('Permission denied', 'NotAllowedError'),
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_allowed'),
    ).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_found error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('No camera', 'NotFoundError'),
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_found'),
    ).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_supported error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('Not supported', 'NotSupportedError'),
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_supported'),
    ).toBeInTheDocument()
  })

  it('shows generic error for unknown errors', async () => {
    mockGetUserMedia.mockRejectedValueOnce(new Error('Unknown'))

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_unknown'),
    ).toBeInTheDocument()
  })

  it('stops webcam when stop button is clicked', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    await user.click(screen.getByText('sign_language.stop_camera'))

    expect(mockTrackStop).toHaveBeenCalled()
    expect(screen.getByText('sign_language.start_camera')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<WebcamCapture className="test-class" />)
    expect(container.firstElementChild).toHaveClass('test-class')
  })

  it('renders hidden canvas for frame capture', () => {
    const { container } = render(<WebcamCapture />)
    const canvas = container.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
    expect(canvas).toHaveAttribute('aria-hidden', 'true')
  })

  it('shows captioning description when streaming', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(screen.getByText('sign_language.continuous_description')).toBeInTheDocument()
  })

  it('shows caption display area with glosses label when streaming', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(screen.getByText('sign_language.captioning_glosses')).toBeInTheDocument()
    expect(screen.getByText('sign_language.captioning_translation')).toBeInTheDocument()
  })

  it('has an sr-only live region for captioning status announcements', () => {
    render(<WebcamCapture />)
    const liveRegion = document.querySelector('[aria-live="assertive"][aria-atomic="true"]')
    expect(liveRegion).toBeInTheDocument()
    expect(liveRegion).toHaveClass('sr-only')
  })

  it('stop camera button has focus-visible outline', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    const stopBtn = screen.getByText('sign_language.stop_camera').closest('button')
    expect(stopBtn).toBeInTheDocument()
    expect(stopBtn?.className).toContain('focus-visible:outline-2')
  })

  it('announces captioning status to screen reader when toggled', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    // Start captioning
    await user.click(screen.getByText('sign_language.continuous_start'))
    const liveRegion = document.querySelector('[aria-live="assertive"][aria-atomic="true"]')
    expect(liveRegion?.textContent).toBe('sign_language.continuous_active')
  })
})
