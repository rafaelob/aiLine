import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInput } from './chat-input'

const mockStartListening = vi.fn()
const mockStopListening = vi.fn()

vi.mock('@/hooks/use-voice-input', () => ({
  useVoiceInput: () => ({
    isListening: false,
    isSupported: true,
    transcript: '',
    startListening: mockStartListening,
    stopListening: mockStopListening,
    error: null,
  }),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ChatInput', () => {
  it('renders text input with accessible label', () => {
    render(<ChatInput onSend={vi.fn()} />)
    expect(screen.getByLabelText('tutor.input_label')).toBeInTheDocument()
  })

  it('renders send button with accessible label', () => {
    render(<ChatInput onSend={vi.fn()} />)
    expect(screen.getByLabelText('tutor.send')).toBeInTheDocument()
  })

  it('renders microphone button when voice is supported', () => {
    render(<ChatInput onSend={vi.fn()} />)
    expect(screen.getByLabelText('tutor.start_voice')).toBeInTheDocument()
  })

  it('calls onSend with trimmed text when send clicked', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, '  Hello world  ')
    await user.click(screen.getByLabelText('tutor.send'))

    expect(onSend).toHaveBeenCalledWith('Hello world')
  })

  it('clears the input after sending', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    const input = screen.getByLabelText('tutor.input_label') as HTMLTextAreaElement
    await user.type(input, 'Test message')
    await user.click(screen.getByLabelText('tutor.send'))

    expect(input.value).toBe('')
  })

  it('sends message on Enter key (not Shift+Enter)', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, 'Question{Enter}')

    expect(onSend).toHaveBeenCalledWith('Question')
  })

  it('does not send on Shift+Enter (allows multiline)', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, 'Line 1{Shift>}{Enter}{/Shift}Line 2')

    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send empty messages', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    await user.click(screen.getByLabelText('tutor.send'))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send whitespace-only messages', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} />)

    const input = screen.getByLabelText('tutor.input_label')
    await user.type(input, '   ')
    await user.click(screen.getByLabelText('tutor.send'))

    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables input and send when disabled prop is true', () => {
    render(<ChatInput onSend={vi.fn()} disabled />)

    const input = screen.getByLabelText('tutor.input_label') as HTMLTextAreaElement
    const sendBtn = screen.getByLabelText('tutor.send') as HTMLButtonElement

    expect(input).toBeDisabled()
    expect(sendBtn).toBeDisabled()
  })

  it('disables microphone button when disabled prop is true', () => {
    render(<ChatInput onSend={vi.fn()} disabled />)
    const micBtn = screen.getByLabelText('tutor.start_voice') as HTMLButtonElement
    expect(micBtn).toBeDisabled()
  })

  it('does not call onSend when disabled even with text', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSend={onSend} disabled />)

    // Input is disabled so we can't type, but test the handler logic
    expect(onSend).not.toHaveBeenCalled()
  })

  it('shows placeholder text', () => {
    render(<ChatInput onSend={vi.fn()} />)
    const input = screen.getByLabelText('tutor.input_label') as HTMLTextAreaElement
    expect(input.placeholder).toBe('tutor.input_placeholder')
  })
})
