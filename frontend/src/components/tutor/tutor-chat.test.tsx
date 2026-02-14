import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TutorChat } from './tutor-chat'

// Mock the tutor SSE hook — dynamic return value via mockReturnValue
const mockSendMessage = vi.fn()
const mockCancel = vi.fn()
const mockReset = vi.fn()

let hookState = {
  sendMessage: mockSendMessage,
  cancel: mockCancel,
  messages: [] as Array<{ id: string; role: 'user' | 'assistant'; content: string }>,
  isStreaming: false,
  error: null as string | null,
  sessionId: null as string | null,
  reset: mockReset,
}

vi.mock('@/hooks/use-tutor-sse', () => ({
  useTutorSSE: () => hookState,
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
  // Reset to default empty state
  hookState = {
    sendMessage: mockSendMessage,
    cancel: mockCancel,
    messages: [],
    isStreaming: false,
    error: null,
    sessionId: null,
    reset: mockReset,
  }
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

  it('renders messages when present and hides welcome', () => {
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Hello' },
      { id: 'msg-2', role: 'assistant', content: 'Hi there!' },
    ]

    render(<TutorChat />)

    expect(screen.queryByText('tutor.welcome_title')).not.toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('renders messages area with log role for chat semantics', () => {
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Test message' },
    ]

    render(<TutorChat />)

    const log = screen.getByRole('log', { name: 'tutor.messages_label' })
    expect(log).toBeInTheDocument()
  })

  it('shows error banner when error is present', () => {
    hookState.error = 'Connection lost'

    render(<TutorChat />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Connection lost')
  })

  it('shows stop generating button while streaming', () => {
    hookState.isStreaming = true
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Tell me about math' },
      { id: 'msg-2', role: 'assistant', content: 'Math is...' },
    ]

    render(<TutorChat />)

    expect(screen.getByText('tutor.stop_generating')).toBeInTheDocument()
  })

  it('calls cancel when stop generating is clicked', async () => {
    hookState.isStreaming = true
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Tell me about math' },
      { id: 'msg-2', role: 'assistant', content: 'Math is...' },
    ]
    const user = userEvent.setup()

    render(<TutorChat />)

    await user.click(screen.getByText('tutor.stop_generating'))
    expect(mockCancel).toHaveBeenCalled()
  })

  it('does not show stop button when not streaming', () => {
    hookState.isStreaming = false

    render(<TutorChat />)

    expect(screen.queryByText('tutor.stop_generating')).not.toBeInTheDocument()
  })

  it('shows thinking indicator when streaming with empty assistant message', () => {
    hookState.isStreaming = true
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Question' },
      { id: 'msg-2', role: 'assistant', content: '' },
    ]

    render(<TutorChat />)

    expect(screen.getByText('tutor.thinking')).toBeInTheDocument()
  })

  it('does not show thinking indicator when assistant has content', () => {
    hookState.isStreaming = true
    hookState.messages = [
      { id: 'msg-1', role: 'user', content: 'Question' },
      { id: 'msg-2', role: 'assistant', content: 'Some response' },
    ]

    render(<TutorChat />)

    expect(screen.queryByText('tutor.thinking')).not.toBeInTheDocument()
  })
})
