'use client'

import { useState, useCallback, useRef } from 'react'
import { useTranslations, useLocale } from 'next-intl'
import { cn } from '@/lib/cn'
import { useVoiceInput } from '@/hooks/use-voice-input'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

/**
 * Chat input bar with text field and voice input button.
 * Voice input uses WebSpeech API with silence auto-submit.
 */
export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const t = useTranslations('tutor')
  const locale = useLocale()
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleVoiceTranscript = useCallback(
    (transcript: string) => {
      if (transcript.trim()) {
        onSend(transcript.trim())
        setText('')
      }
    },
    [onSend]
  )

  const {
    isListening,
    isSupported: voiceSupported,
    transcript,
    startListening,
    stopListening,
    error: voiceError,
  } = useVoiceInput({
    locale,
    onTranscript: handleVoiceTranscript,
    silenceTimeout: 1500,
  })

  // Show live transcript in the text field (derived — no effect needed)
  const displayText = isListening && transcript ? transcript : text

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    inputRef.current?.focus()
  }, [text, disabled, onSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  return (
    <div className="border-t border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      {/* Voice error */}
      {voiceError && (
        <p className="text-xs text-[var(--color-error)] mb-2" role="alert">
          {t(`voice_error_${voiceError}`, { defaultValue: t('voice_error_generic') })}
        </p>
      )}

      <div className="flex items-end gap-2">
        {/* Voice input button */}
        {voiceSupported && (
          <button
            type="button"
            onClick={isListening ? stopListening : startListening}
            disabled={disabled}
            className={cn(
              'flex items-center justify-center w-10 h-10 rounded-full shrink-0',
              'transition-all',
              isListening
                ? 'bg-[var(--color-error)] text-white animate-pulse'
                : 'bg-[var(--color-surface-elevated)] text-[var(--color-muted)] hover:text-[var(--color-text)]',
              'disabled:opacity-40 disabled:cursor-not-allowed'
            )}
            aria-label={isListening ? t('stop_voice') : t('start_voice')}
          >
            <MicIcon active={isListening} />
          </button>
        )}

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={displayText}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isListening ? t('listening_placeholder') : t('input_placeholder')
            }
            disabled={disabled}
            rows={1}
            className={cn(
              'w-full resize-none rounded-[var(--radius-lg)] border p-3 pr-12',
              'bg-[var(--color-bg)] border-[var(--color-border)]',
              'text-[var(--color-text)] text-sm',
              'placeholder:text-[var(--color-muted)]',
              'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'max-h-32 overflow-y-auto'
            )}
            aria-label={t('input_label')}
          />
        </div>

        {/* Send button */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !displayText.trim()}
          className={cn(
            'flex items-center justify-center w-10 h-10 rounded-full shrink-0',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'hover:bg-[var(--color-primary-hover)] transition-colors',
            'disabled:opacity-40 disabled:cursor-not-allowed'
          )}
          aria-label={t('send')}
        >
          <SendIcon />
        </button>
      </div>

      {/* Listening indicator */}
      {isListening && (
        <div className="flex items-center gap-2 mt-2 text-xs text-[var(--color-error)]">
          <span className="flex gap-0.5">
            <span className="w-1 h-3 bg-[var(--color-error)] rounded-full animate-pulse" />
            <span className="w-1 h-4 bg-[var(--color-error)] rounded-full animate-pulse delay-75" />
            <span className="w-1 h-2 bg-[var(--color-error)] rounded-full animate-pulse delay-150" />
          </span>
          {t('listening')}
        </div>
      )}
    </div>
  )
}

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill={active ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path d="M19 10v2a7 7 0 01-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}
