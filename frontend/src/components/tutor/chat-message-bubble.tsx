'use client'

import { useCallback, useState, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { MarkdownWithMermaid } from '@/components/shared/markdown-with-mermaid'
import type { ChatMessage } from '@/types/tutor'

interface ChatMessageBubbleProps {
  message: ChatMessage
  isStreaming?: boolean
}

/**
 * Individual chat message bubble.
 * User messages right-aligned, assistant messages left-aligned.
 * Supports TTS read-aloud and mermaid diagram rendering.
 */
export function ChatMessageBubble({
  message,
  isStreaming = false,
}: ChatMessageBubbleProps) {
  const t = useTranslations('tutor')
  const isUser = message.role === 'user'
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [copied, setCopied] = useState(false)

  const relativeTime = useMemo(() => {
    if (!message.timestamp) return null
    try {
      const date = new Date(message.timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMin = Math.floor(diffMs / 60000)
      if (diffMin < 1) return t('just_now')
      if (diffMin < 60) return `${diffMin} min`
      const diffHrs = Math.floor(diffMin / 60)
      return `${diffHrs}h`
    } catch {
      return null
    }
  }, [message.timestamp, t])

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API not available
    }
  }, [message.content])

  const handleReadAloud = useCallback(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    const utterance = new SpeechSynthesisUtterance(message.content)
    // Use locale from document for correct TTS language
    const docLang = typeof document !== 'undefined' ? document.documentElement.lang : 'pt-BR'
    utterance.lang = docLang || 'pt-BR'
    utterance.rate = 0.9
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utterance)
    setIsSpeaking(true)
  }, [message.content, isSpeaking])

  return (
    <div
      className={cn(
        'flex gap-3 max-w-[85%]',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
      role="listitem"
    >
      {/* Avatar */}
      {isUser ? (
        <div
          className="flex items-center justify-center w-8 h-8 rounded-full shrink-0"
          style={{ background: 'var(--color-primary)' }}
          aria-hidden="true"
        >
          <UserIcon className="text-white" />
        </div>
      ) : (
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0 icon-orb"
          style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
          aria-hidden="true"
        >
          <BotIcon className="text-white" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          'rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)] rounded-br-md'
            : 'glass-bubble-ai text-[var(--color-text)] rounded-bl-md'
        )}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="space-y-1">
            <MarkdownWithMermaid
              content={message.content}
              textClassName="text-sm text-[var(--color-text)] whitespace-pre-wrap"
            />
            {isStreaming && (
              <span
                className="inline-block w-1.5 h-4 rounded-sm animate-pulse"
                style={{ background: 'linear-gradient(to bottom, var(--color-primary), var(--color-secondary))' }}
                aria-label={t('typing')}
              />
            )}
          </div>
        )}

        {/* Action buttons for assistant messages */}
        {!isUser && !isStreaming && message.content && (
          <div className="mt-2 flex items-center gap-3">
            <button
              type="button"
              onClick={handleReadAloud}
              className={cn(
                'flex items-center gap-1 text-xs',
                'text-[var(--color-muted)] hover:text-[var(--color-primary)]',
                'hover:bg-[var(--color-primary)]/5 rounded-md px-1.5 py-0.5',
                'transition-all duration-200'
              )}
              aria-label={isSpeaking ? t('stop_reading') : t('read_aloud')}
            >
              {isSpeaking ? <StopIcon /> : <SpeakerIcon />}
              {isSpeaking ? t('stop_reading') : t('read_aloud')}
            </button>
            <button
              type="button"
              onClick={handleCopy}
              className={cn(
                'flex items-center gap-1 text-xs',
                'text-[var(--color-muted)] hover:text-[var(--color-primary)]',
                'hover:bg-[var(--color-primary)]/5 rounded-md px-1.5 py-0.5',
                'transition-all duration-200'
              )}
              aria-label={copied ? t('copied') : t('copy')}
            >
              {copied ? <CheckIcon /> : <CopyIcon />}
              {copied ? t('copied') : t('copy')}
            </button>
          </div>
        )}

        {/* Timestamp */}
        {relativeTime && (
          <p className="mt-1 text-[10px] text-[var(--color-muted)] opacity-60">
            {relativeTime}
          </p>
        )}
      </div>
    </div>
  )
}

function UserIcon({ className = '' }: { className?: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}

function BotIcon({ className = '' }: { className?: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8" y2="16" />
      <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
  )
}

function SpeakerIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  )
}

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}
