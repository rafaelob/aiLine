'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useTTSKaraoke } from '@/hooks/use-tts-karaoke'

const SPEED_OPTIONS = [
  { value: 0.75, label: '0.75x' },
  { value: 1, label: '1x' },
  { value: 1.5, label: '1.5x' },
] as const

interface KaraokeReaderProps {
  text: string
  lang?: string
  className?: string
}

/**
 * TTS Karaoke reader: displays text with word-by-word highlighting
 * synchronized with speech synthesis. Includes play/pause, stop, and speed controls.
 */
export function KaraokeReader({ text, lang = 'pt-BR', className }: KaraokeReaderProps) {
  const t = useTranslations('accessibility')
  const { isPlaying, currentWordIndex, speed, speak, pause, resume, stop, setSpeed } =
    useTTSKaraoke()

  const words = useMemo(() => text.split(/\s+/).filter(Boolean), [text])

  const totalWords = words.length
  const progress = currentWordIndex >= 0 ? Math.round((currentWordIndex / totalWords) * 100) : 0

  function handlePlayPause() {
    if (isPlaying) {
      pause()
    } else if (currentWordIndex >= 0) {
      resume()
    } else {
      speak(text, lang)
    }
  }

  return (
    <div className={cn('rounded-[var(--radius-md)] border border-[var(--color-border)] p-4', className)}>
      {/* Controls */}
      <div className="flex items-center gap-3 mb-3">
        <button
          type="button"
          onClick={handlePlayPause}
          aria-label={isPlaying ? t('ttsPause') : t('ttsPlay')}
          className={cn(
            'rounded-[var(--radius-sm)] px-3 py-1.5 text-sm font-medium',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'hover:opacity-90 transition-opacity'
          )}
        >
          {isPlaying ? (
            <span className="flex items-center gap-1.5">
              <PauseIcon />
              {t('ttsPause')}
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <PlayIcon />
              {t('ttsPlay')}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={stop}
          aria-label={t('ttsStop')}
          disabled={currentWordIndex < 0}
          className={cn(
            'rounded-[var(--radius-sm)] px-3 py-1.5 text-sm',
            'border border-[var(--color-border)] text-[var(--color-text)]',
            'hover:bg-[var(--color-surface-elevated)] transition-colors',
            'disabled:opacity-40 disabled:cursor-not-allowed'
          )}
        >
          {t('ttsStop')}
        </button>

        {/* Speed selector */}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-xs text-[var(--color-muted)]">{t('ttsSpeed')}:</span>
          {SPEED_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setSpeed(opt.value)}
              aria-pressed={speed === opt.value}
              className={cn(
                'rounded-[var(--radius-sm)] px-2 py-0.5 text-xs transition-colors',
                speed === opt.value
                  ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                  : 'border border-[var(--color-border)] text-[var(--color-muted)] hover:bg-[var(--color-surface-elevated)]'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Progress bar */}
      {currentWordIndex >= 0 && (
        <div
          className="h-1 rounded-full bg-[var(--color-border)] mb-3 overflow-hidden"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full bg-[var(--color-primary)] transition-[width] duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Karaoke text */}
      <p className="text-[var(--color-text)] leading-relaxed text-base" aria-live="polite">
        {words.map((word, i) => (
          <span key={`${i}-${word}`}>
            <span
              className={cn(
                'rounded px-0.5 transition-colors duration-150',
                i === currentWordIndex && 'bg-yellow-300 text-black dark:bg-yellow-400 dark:text-black'
              )}
            >
              {word}
            </span>
            {i < words.length - 1 ? ' ' : ''}
          </span>
        ))}
      </p>
    </div>
  )
}

function PlayIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
      <path d="M3 1.5v11l9-5.5z" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
      <rect x="2" y="1" width="3.5" height="12" rx="0.5" />
      <rect x="8.5" y="1" width="3.5" height="12" rx="0.5" />
    </svg>
  )
}
