import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WebcamCapture } from './webcam-capture'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
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
    classify: vi.fn(),
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

  it('renders webcam and result headings', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.webcam')).toBeInTheDocument()
    expect(screen.getByText('sign_language.result')).toBeInTheDocument()
  })

  it('shows start camera button initially', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.start_camera')).toBeInTheDocument()
  })

  it('shows webcam off message initially', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.webcam_off')).toBeInTheDocument()
  })

  it('shows no result message initially', () => {
    render(<WebcamCapture />)
    expect(screen.getByText('sign_language.no_result')).toBeInTheDocument()
  })

  it('calls getUserMedia when start camera is clicked', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
  })

  it('shows recognize and stop buttons after starting camera', async () => {
    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(screen.getByText('sign_language.recognize')).toBeInTheDocument()
    expect(screen.getByText('sign_language.stop_camera')).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_allowed error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('Permission denied', 'NotAllowedError')
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_allowed')
    ).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_found error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('No camera', 'NotFoundError')
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_found')
    ).toBeInTheDocument()
  })

  it('shows error message on getUserMedia not_supported error', async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException('Not supported', 'NotSupportedError')
    )

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_not_supported')
    ).toBeInTheDocument()
  })

  it('shows generic error for unknown errors', async () => {
    mockGetUserMedia.mockRejectedValueOnce(new Error('Unknown'))

    render(<WebcamCapture />)
    await user.click(screen.getByText('sign_language.start_camera'))

    expect(
      screen.getByText('sign_language.error_unknown')
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
})
