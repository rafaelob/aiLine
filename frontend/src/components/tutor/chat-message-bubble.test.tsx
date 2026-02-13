import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatMessageBubble } from './chat-message-bubble'
import type { ChatMessage } from '@/types/tutor'

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

function makeMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: 'msg-1',
    role: 'assistant',
    content: 'Hello from the tutor',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

const mockSpeak = vi.fn()
const mockCancel = vi.fn()
const mockWriteText = vi.fn().mockResolvedValue(undefined)

// Mock SpeechSynthesisUtterance (not available in jsdom)
class MockSpeechSynthesisUtterance {
  lang = ''
  rate = 1
  text: string
  onend: (() => void) | null = null
  onerror: (() => void) | null = null
  constructor(text: string) {
    this.text = text
  }
}
vi.stubGlobal('SpeechSynthesisUtterance', MockSpeechSynthesisUtterance)

beforeEach(() => {
  vi.clearAllMocks()
  // Mock speechSynthesis
  Object.defineProperty(window, 'speechSynthesis', {
    writable: true,
    configurable: true,
    value: {
      speak: mockSpeak,
      cancel: mockCancel,
    },
  })
  // Mock clipboard with configurable so userEvent can also work
  Object.defineProperty(navigator, 'clipboard', {
    writable: true,
    configurable: true,
    value: {
      writeText: mockWriteText,
      readText: vi.fn().mockResolvedValue(''),
      read: vi.fn().mockResolvedValue([]),
      write: vi.fn().mockResolvedValue(undefined),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    },
  })
})

describe('ChatMessageBubble', () => {
  it('renders user message with content', () => {
    render(
      <ChatMessageBubble message={makeMessage({ role: 'user', content: 'Hi there' })} />
    )
    expect(screen.getByText('Hi there')).toBeInTheDocument()
  })

  it('renders assistant message with content', () => {
    render(
      <ChatMessageBubble message={makeMessage({ content: 'AI response' })} />
    )
    expect(screen.getByText('AI response')).toBeInTheDocument()
  })

  it('renders with role="listitem" for accessibility', () => {
    const { container } = render(
      <ChatMessageBubble message={makeMessage()} />
    )
    expect(container.querySelector('[role="listitem"]')).toBeInTheDocument()
  })

  it('shows streaming cursor when isStreaming is true for assistant', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'assistant', content: 'partial' })}
        isStreaming={true}
      />
    )
    expect(screen.getByLabelText('tutor.typing')).toBeInTheDocument()
  })

  it('does not show streaming cursor when isStreaming is false', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'assistant', content: 'complete' })}
        isStreaming={false}
      />
    )
    expect(screen.queryByLabelText('tutor.typing')).not.toBeInTheDocument()
  })

  it('does not show streaming cursor for user messages even if isStreaming', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'user', content: 'my message' })}
        isStreaming={true}
      />
    )
    expect(screen.queryByLabelText('tutor.typing')).not.toBeInTheDocument()
  })

  it('shows action buttons for assistant messages when not streaming', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'assistant', content: 'response' })}
        isStreaming={false}
      />
    )
    expect(screen.getByLabelText('tutor.read_aloud')).toBeInTheDocument()
    expect(screen.getByLabelText('tutor.copy')).toBeInTheDocument()
  })

  it('does not show action buttons for user messages', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'user', content: 'msg' })}
      />
    )
    expect(screen.queryByLabelText('tutor.read_aloud')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('tutor.copy')).not.toBeInTheDocument()
  })

  it('does not show action buttons while streaming', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'assistant', content: 'partial' })}
        isStreaming={true}
      />
    )
    expect(screen.queryByLabelText('tutor.read_aloud')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('tutor.copy')).not.toBeInTheDocument()
  })

  it('copies message content when copy button is clicked', async () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ content: 'Copy this text' })}
      />
    )
    fireEvent.click(screen.getByLabelText('tutor.copy'))
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith('Copy this text')
    })
  })

  it('shows copied label after clicking copy', async () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ content: 'Copy this' })}
      />
    )
    fireEvent.click(screen.getByLabelText('tutor.copy'))
    await waitFor(() => {
      expect(screen.getByLabelText('tutor.copied')).toBeInTheDocument()
    })
  })

  it('triggers speechSynthesis when read aloud is clicked', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ content: 'Read me out loud' })}
      />
    )
    fireEvent.click(screen.getByLabelText('tutor.read_aloud'))
    expect(mockSpeak).toHaveBeenCalled()
  })

  it('renders timestamp when provided', () => {
    const ts = new Date(Date.now() - 120000).toISOString() // 2 min ago
    render(
      <ChatMessageBubble message={makeMessage({ timestamp: ts })} />
    )
    expect(screen.getByText('2 min')).toBeInTheDocument()
  })

  it('renders "just now" for very recent timestamps', () => {
    const ts = new Date().toISOString()
    render(
      <ChatMessageBubble message={makeMessage({ timestamp: ts })} />
    )
    expect(screen.getByText('tutor.just_now')).toBeInTheDocument()
  })

  it('renders user avatar icon for user messages', () => {
    const { container } = render(
      <ChatMessageBubble message={makeMessage({ role: 'user' })} />
    )
    const avatars = container.querySelectorAll('[aria-hidden="true"]')
    expect(avatars.length).toBeGreaterThan(0)
  })

  it('renders bot avatar icon for assistant messages', () => {
    const { container } = render(
      <ChatMessageBubble message={makeMessage({ role: 'assistant' })} />
    )
    const avatars = container.querySelectorAll('[aria-hidden="true"]')
    expect(avatars.length).toBeGreaterThan(0)
  })

  it('does not show action buttons when content is empty', () => {
    render(
      <ChatMessageBubble
        message={makeMessage({ role: 'assistant', content: '' })}
      />
    )
    expect(screen.queryByLabelText('tutor.read_aloud')).not.toBeInTheDocument()
  })
})
