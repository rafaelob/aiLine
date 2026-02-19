import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TtsPlayer } from './tts-player'

describe('TtsPlayer', () => {
  const user = userEvent.setup()
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn().mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/tts/voices')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ voices: [] }),
        })
      }
      if (typeof url === 'string' && url.includes('/tts/synthesize')) {
        return Promise.resolve({
          ok: true,
          blob: async () => new Blob(['audio'], { type: 'audio/mpeg' }),
        })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders with proper ARIA region', async () => {
    await act(async () => {
      render(<TtsPlayer text="Hello world" />)
    })
    const region = screen.getByRole('region')
    expect(region).toHaveAttribute('aria-label', 'tts.player_label')
  })

  it('renders play button with correct label', async () => {
    await act(async () => {
      render(<TtsPlayer text="Hello world" />)
    })
    const btn = screen.getByRole('button', { name: 'tts.play' })
    expect(btn).toBeInTheDocument()
  })

  it('disables play button when text is empty', async () => {
    await act(async () => {
      render(<TtsPlayer text="" />)
    })
    const btn = screen.getByRole('button', { name: 'tts.play' })
    expect(btn).toBeDisabled()
  })

  it('renders speed selector with all options', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    const speedSelect = document.getElementById('tts-speed') as HTMLSelectElement
    expect(speedSelect).toBeInTheDocument()
    const options = speedSelect.querySelectorAll('option')
    expect(options).toHaveLength(6)
  })

  it('renders language selector with 3 languages', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    const langSelect = document.getElementById('tts-language') as HTMLSelectElement
    expect(langSelect).toBeInTheDocument()
    const options = langSelect.querySelectorAll('option')
    expect(options).toHaveLength(3)
  })

  it('renders voice selector', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    const voiceSelect = document.getElementById('tts-voice') as HTMLSelectElement
    expect(voiceSelect).toBeInTheDocument()
  })

  it('calls synthesize on play button click', async () => {
    await act(async () => {
      render(<TtsPlayer text="Hello world" />)
    })
    const btn = screen.getByRole('button', { name: 'tts.play' })

    await act(async () => {
      await user.click(btn)
    })

    await waitFor(() => {
      const synthCall = fetchSpy.mock.calls.find(
        (c: unknown[]) => typeof c[0] === 'string' && (c[0] as string).includes('/tts/synthesize'),
      )
      expect(synthCall).toBeTruthy()
    })
  })

  it('shows error message on synthesis failure', async () => {
    fetchSpy.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/tts/voices')) {
        return Promise.resolve({ ok: true, json: async () => ({ voices: [] }) })
      }
      return Promise.resolve({ ok: false, status: 500 })
    })

    await act(async () => {
      render(<TtsPlayer text="Hello world" />)
    })
    const btn = screen.getByRole('button', { name: 'tts.play' })

    await act(async () => {
      await user.click(btn)
    })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('tts.error')
    })
  })

  it('has progress bar disabled when idle', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    const slider = screen.getByRole('slider')
    expect(slider).toBeDisabled()
  })

  it('fetches voices on mount', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })

    await waitFor(() => {
      const voiceCall = fetchSpy.mock.calls.find(
        (c: unknown[]) => typeof c[0] === 'string' && (c[0] as string).includes('/tts/voices'),
      )
      expect(voiceCall).toBeTruthy()
    })
  })

  it('applies custom className', async () => {
    let container: HTMLElement
    await act(async () => {
      const result = render(<TtsPlayer text="Test" className="my-custom" />)
      container = result.container
    })
    expect(container!.firstElementChild).toHaveClass('my-custom')
  })

  it('has screen reader live region', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    const srOnly = document.querySelector('.sr-only[aria-live="polite"]')
    expect(srOnly).toBeInTheDocument()
  })

  it('displays time format correctly', async () => {
    await act(async () => {
      render(<TtsPlayer text="Test" />)
    })
    // Initial time should be 0:00
    const times = screen.getAllByText('0:00')
    expect(times.length).toBeGreaterThanOrEqual(1)
  })
})
