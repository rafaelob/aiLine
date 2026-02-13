import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TutorChat } from './tutor-chat'

// Mock the tutor SSE hook
const mockSendMessage = vi.fn()
const mockCancel = vi.fn()
const mockReset = vi.fn()

vi.mock('@/hooks/use-tutor-sse', () => ({
  useTutorSSE: () => ({
    sendMessage: mockSendMessage,
    cancel: mockCancel,
    messages: [],
    isStreaming: false,
    error: null,
    sessionId: null,
    reset: mockReset,
  }),
}))

// Mock the voice input hook
vi.mock('@/hooks/use-voice-input', () => ({
  useVoiceInput: () => ({
    isListening: false,
    isSupported: true,
    transcript: '',
    startListening: vi.fn(),
    stopListening: vi.fn(),
    error: null,
  }),
}))

// Mock mermaid-loader for MarkdownWithMermaid
vi.mock('@/lib/mermaid-loader', () => ({
  loadMermaid: () =>
    Promise.resolve({
      initialize: vi.fn(),
      render: vi.fn().mockResolvedValue({ svg: '<svg></svg>' }),
    }),
}))

// Mock useThemeContext
vi.mock('@/hooks/use-theme-context', () => ({
  useThemeContext: () => 'standard',
}))

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
  // JSDOM does not implement scrollTo
  Element.prototype.scrollTo = vi.fn()
})

describe('TutorChat', () => {
  it('renders the welcome screen when no messages', () => {
    render(<TutorChat />)
    expect(screen.getByText('tutor.welcome_title')).toBeInTheDocument()
    expect(screen.getByText('tutor.welcome_description')).toBeInTheDocument()
  })

  it('renders example prompt buttons', () => {
    render(<TutorChat />)
    expect(screen.getByText('tutor.example_1')).toBeInTheDocument()
    expect(screen.getByText('tutor.example_2')).toBeInTheDocument()
    expect(screen.getByText('tutor.example_3')).toBeInTheDocument()
  })

  it('sends message when example prompt clicked', async () => {
    const user = userEvent.setup()
    render(<TutorChat />)
    await user.click(screen.getByText('tutor.example_1'))
    expect(mockSendMessage).toHaveBeenCalledWith('tutor.example_1')
  })

  it('renders the message input and send button', () => {
    render(<TutorChat />)
    expect(screen.getByLabelText('tutor.input_label')).toBeInTheDocument()
    expect(screen.getByLabelText('tutor.send')).toBeInTheDocument()
  })

  it('renders microphone button for voice input', () => {
    render(<TutorChat />)
    expect(screen.getByLabelText('tutor.start_voice')).toBeInTheDocument()
  })

  it('sends text message on submit', async () => {
    const user = userEvent.setup()
    render(<TutorChat />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, 'Hello tutor')
    await user.click(screen.getByLabelText('tutor.send'))

    expect(mockSendMessage).toHaveBeenCalledWith('Hello tutor')
  })

  it('sends text message on Enter key', async () => {
    const user = userEvent.setup()
    render(<TutorChat />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, 'Question{Enter}')

    expect(mockSendMessage).toHaveBeenCalledWith('Question')
  })

  it('does not send empty messages', async () => {
    const user = userEvent.setup()
    render(<TutorChat />)

    await user.click(screen.getByLabelText('tutor.send'))
    expect(mockSendMessage).not.toHaveBeenCalled()
  })
})
