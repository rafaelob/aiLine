import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { KaraokeReader } from './karaoke-reader'

const mockSpeak = vi.fn()
const mockPause = vi.fn()
const mockResume = vi.fn()
const mockStop = vi.fn()
const mockSetSpeed = vi.fn()

vi.mock('@/hooks/use-tts-karaoke', () => ({
  useTTSKaraoke: () => ({
    isPlaying: false,
    currentWordIndex: -1,
    speed: 1,
    speak: mockSpeak,
    pause: mockPause,
    resume: mockResume,
    stop: mockStop,
    setSpeed: mockSetSpeed,
  }),
}))

describe('KaraokeReader', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all words from text', () => {
    render(<KaraokeReader text="Hello world test" />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('world')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
  })

  it('renders play button with translated label', () => {
    render(<KaraokeReader text="Hello" />)
    expect(screen.getByLabelText('accessibility.ttsPlay')).toBeInTheDocument()
  })

  it('renders stop button', () => {
    render(<KaraokeReader text="Hello" />)
    expect(screen.getByText('accessibility.ttsStop')).toBeInTheDocument()
  })

  it('renders speed buttons', () => {
    render(<KaraokeReader text="Hello" />)
    expect(screen.getByText('0.75x')).toBeInTheDocument()
    expect(screen.getByText('1x')).toBeInTheDocument()
    expect(screen.getByText('1.5x')).toBeInTheDocument()
  })

  it('calls speak when play is clicked', async () => {
    render(<KaraokeReader text="Hello world" />)
    const playBtn = screen.getByLabelText('accessibility.ttsPlay')
    await user.click(playBtn)
    expect(mockSpeak).toHaveBeenCalledWith('Hello world', 'pt-BR')
  })

  it('calls setSpeed when speed button is clicked', async () => {
    render(<KaraokeReader text="Hello" />)
    await user.click(screen.getByText('1.5x'))
    expect(mockSetSpeed).toHaveBeenCalledWith(1.5)
  })

  it('stop button is disabled when nothing is playing', () => {
    render(<KaraokeReader text="Hello" />)
    const stopBtn = screen.getByText('accessibility.ttsStop')
    expect(stopBtn).toBeDisabled()
  })
})
