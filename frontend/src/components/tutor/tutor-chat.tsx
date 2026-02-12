'use client'

import { useEffect, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useTutorSSE } from '@/hooks/use-tutor-sse'
import { ChatMessageBubble } from './chat-message-bubble'
import { ChatInput } from './chat-input'

/**
 * Main tutor chat interface.
 * Shows message history, streams AI responses via SSE, and supports voice input.
 */
export function TutorChat() {
  const t = useTranslations('tutor')
  const { sendMessage, messages, isStreaming, error } = useTutorSSE()
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const isEmpty = messages.length === 0

  return (
    <div
      className={cn(
        'flex flex-col h-[calc(100vh-12rem)]',
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] overflow-hidden'
      )}
    >
      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="list"
        aria-label={t('messages_label')}
      >
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <TutorWelcomeIcon />
            <h2 className="text-lg font-semibold text-[var(--color-text)] mt-4">
              {t('welcome_title')}
            </h2>
            <p className="text-sm text-[var(--color-muted)] mt-2 max-w-md">
              {t('welcome_description')}
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center">
              {(['example_1', 'example_2', 'example_3'] as const).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => sendMessage(t(key))}
                  className={cn(
                    'px-4 py-2 text-xs rounded-full',
                    'border border-[var(--color-border)]',
                    'text-[var(--color-text)]',
                    'hover:bg-[var(--color-surface-elevated)] transition-colors'
                  )}
                >
                  {t(key)}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessageBubble
            key={msg.id}
            message={msg}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        {/* Thinking indicator */}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && messages[messages.length - 1].content === '' && (
          <div className="flex items-center gap-2 text-sm text-[var(--color-muted)] pl-11">
            <ThinkingDots />
            {t('thinking')}
          </div>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="px-4 py-2 bg-[var(--color-error)]/10 text-[var(--color-error)] text-xs text-center"
        >
          {error}
        </div>
      )}

      {/* Input bar */}
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}

function TutorWelcomeIcon() {
  return (
    <div className="w-16 h-16 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center">
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
        <circle cx="9" cy="10" r="1" fill="var(--color-primary)" />
        <circle cx="12" cy="10" r="1" fill="var(--color-primary)" />
        <circle cx="15" cy="10" r="1" fill="var(--color-primary)" />
      </svg>
    </div>
  )
}

function ThinkingDots() {
  return (
    <span className="flex gap-1" aria-hidden="true">
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted)] animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted)] animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted)] animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  )
}
