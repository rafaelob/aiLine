'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
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
  const { sendMessage, cancel, messages, isStreaming, error } = useTutorSSE()
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const scrollRef = useRef<HTMLDivElement>(null)
  const userScrolledUp = useRef(false)

  // Track whether user has scrolled away from bottom
  const handleScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    userScrolledUp.current = distanceFromBottom > 80
  }, [])

  // Auto-scroll to bottom when new messages arrive (unless user scrolled up)
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    if (userScrolledUp.current) return
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const isEmpty = messages.length === 0

  return (
    <div
      className={cn(
        'flex flex-col flex-1 min-h-0 max-h-[calc(100vh-10rem)] sm:max-h-[calc(100vh-8rem)]',
        'rounded-2xl',
        'glass shadow-[var(--shadow-lg)]',
        'overflow-hidden'
      )}
    >
      {/* Messages area */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
        role="log"
        aria-label={t('messages_label')}
        aria-live="polite"
        aria-relevant="additions"
      >
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            {/* Premium welcome icon with gradient orb */}
            <TutorWelcomeIcon />
            <h2 className="text-lg font-semibold text-[var(--color-text)] mt-5">
              {t('welcome_title')}
            </h2>
            <p className="text-sm text-[var(--color-muted)] mt-2 max-w-md">
              {t('welcome_description')}
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center">
              {(['example_1', 'example_2', 'example_3'] as const).map((key, i) => (
                <motion.button
                  key={key}
                  type="button"
                  aria-label={t(key)}
                  initial={noMotion ? undefined : { opacity: 0, y: 8 }}
                  animate={noMotion ? undefined : { opacity: 1, y: 0 }}
                  transition={noMotion ? undefined : { delay: 0.3 + i * 0.1, type: 'spring', stiffness: 200, damping: 24 }}
                  onClick={() => sendMessage(t(key))}
                  className={cn(
                    'px-4 py-2 text-xs rounded-full',
                    'border border-[var(--color-border)]',
                    'text-[var(--color-text)]',
                    'hover:bg-[var(--color-surface-elevated)]',
                    'hover:border-[var(--color-primary)]/30',
                    'hover:shadow-[0_0_12px_-3px_var(--color-primary)]',
                    'transition-all duration-200'
                  )}
                >
                  {t(key)}
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <motion.div
            key={msg.id}
            initial={noMotion ? undefined : { opacity: 0, y: 16, scale: 0.97 }}
            animate={noMotion ? undefined : { opacity: 1, y: 0, scale: 1 }}
            transition={noMotion ? undefined : {
              type: 'spring',
              stiffness: 200,
              damping: 24,
            }}
          >
            <ChatMessageBubble
              message={msg}
              isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
            />
          </motion.div>
        ))}

        {/* Thinking indicator */}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && messages[messages.length - 1].content === '' && (
          <AuroraThinking />
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

      {/* Stop generating button */}
      {isStreaming && (
        <div className="flex justify-center px-4 py-2 border-t border-[var(--color-border)]">
          <button
            type="button"
            onClick={cancel}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl',
              'border border-[var(--color-border)] text-sm font-medium',
              'text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)]',
              'hover:border-[var(--color-error)]/30',
              'active:scale-95',
              'transition-all duration-200'
            )}
          >
            <StopSquareIcon />
            {t('stop_generating')}
          </button>
        </div>
      )}

      {/* SR-only live region for streaming status */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {isStreaming && messages.length > 0
          ? t('typing')
          : error
            ? error
            : null}
      </div>

      {/* Input bar */}
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}

function TutorWelcomeIcon() {
  return (
    <div className="relative">
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center icon-orb"
        style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
      >
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          <circle cx="9" cy="10" r="1" fill="white" />
          <circle cx="12" cy="10" r="1" fill="white" />
          <circle cx="15" cy="10" r="1" fill="white" />
        </svg>
      </div>
    </div>
  )
}

function StopSquareIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  )
}

function AuroraThinking() {
  const t = useTranslations('tutor')
  return (
    <div className="flex items-center gap-3 pl-11" role="status">
      <div className="relative w-10 h-10">
        {/* Aurora glow blob */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'linear-gradient(-45deg, var(--color-primary), var(--color-secondary), var(--color-success), var(--color-primary))',
            backgroundSize: '400% 400%',
            animation: 'aurora-shift 3s ease infinite',
            filter: 'blur(12px)',
            opacity: 0.7,
          }}
          aria-hidden="true"
        />
        {/* Inner solid dot */}
        <div
          className="absolute inset-2 rounded-full bg-[var(--color-primary)]"
          style={{ animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}
          aria-hidden="true"
        />
      </div>
      <span className="text-sm text-[var(--color-muted)] italic">{t('thinking')}</span>
    </div>
  )
}
