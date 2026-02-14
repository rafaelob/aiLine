'use client'

import { useTranslations } from 'next-intl'
import { AnimatePresence, motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useLibrasCaptioning } from '@/hooks/use-libras-captioning'

interface LibrasCaptioningProps {
  className?: string
}

/**
 * Libras captioning component: displays real-time sign language
 * recognition results with translated Portuguese text.
 *
 * Two-line display:
 * - Raw glosses (small, faint) — the detected sign tokens
 * - Translated text (normal) — fluent Portuguese from LLM
 *
 * Draft text shown in gray, committed text in full color.
 * Includes a confidence indicator and recording toggle.
 */
export function LibrasCaptioning({ className }: LibrasCaptioningProps) {
  const t = useTranslations('sign_language')
  const {
    isRecording,
    rawGlosses,
    draftText,
    committedText,
    confidence,
    connectionStatus,
    error,
    startCaptioning,
    stopCaptioning,
  } = useLibrasCaptioning()

  const confidencePercent = Math.round(confidence * 100)
  const isConnecting = connectionStatus === 'connecting'

  return (
    <div className={cn('flex flex-col gap-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--color-text)]">
          {t('captioning_title')}
        </h3>
        <button
          type="button"
          onClick={isRecording ? stopCaptioning : startCaptioning}
          disabled={isConnecting}
          aria-pressed={isRecording}
          className={cn(
            'rounded-[var(--radius-md)] px-4 py-2',
            'font-medium text-sm transition-colors',
            'focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-[var(--color-primary)]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            isRecording
              ? 'bg-[var(--color-error)] text-white hover:opacity-90'
              : 'bg-[var(--color-primary)] text-[var(--color-on-primary)] hover:opacity-90'
          )}
        >
          {isConnecting
            ? t('captioning_connecting')
            : isRecording
              ? t('captioning_stop')
              : t('captioning_start')}
        </button>
      </div>

      <p className="text-sm text-[var(--color-muted)]">
        {t('captioning_description')}
      </p>

      {/* Caption display area */}
      <div
        className={cn(
          'relative min-h-[120px] rounded-[var(--radius-md)] p-4',
          'border border-[var(--color-border)]',
          'bg-[var(--color-surface-elevated)]',
        )}
        aria-live="polite"
        aria-atomic="false"
      >
        {/* Recording indicator */}
        {isRecording && (
          <div className="absolute right-3 top-3 flex items-center gap-1.5">
            <span
              className="block h-2.5 w-2.5 rounded-full bg-[var(--color-error)]"
              style={{ animation: 'pulse 1.5s ease-in-out infinite' }}
              aria-hidden="true"
            />
            <span className="text-xs text-[var(--color-error)] font-medium">
              {t('captioning_recording')}
            </span>
          </div>
        )}

        {/* Raw glosses line */}
        <div className="mb-2">
          <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
            {t('captioning_glosses')}
          </span>
          <div className="mt-0.5 min-h-[20px] text-sm text-[var(--color-muted)]">
            <AnimatePresence mode="wait">
              {rawGlosses.length > 0 ? (
                <motion.span
                  key={rawGlosses.join('-')}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 0.7, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {rawGlosses.join(' ')}
                </motion.span>
              ) : (
                <span className="opacity-40">---</span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Translation line */}
        <div>
          <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
            {t('captioning_translation')}
          </span>
          <div className="mt-0.5 min-h-[24px] text-base">
            {committedText || draftText ? (
              <p>
                {committedText && (
                  <span className="text-[var(--color-text)]">{committedText}</span>
                )}
                {committedText && draftText && ' '}
                {draftText && (
                  <motion.span
                    className="text-[var(--color-muted)]"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                    transition={{ duration: 0.15 }}
                  >
                    {draftText}
                  </motion.span>
                )}
              </p>
            ) : isRecording ? (
              <span className="text-sm text-[var(--color-muted)] opacity-50">
                {t('captioning_draft')}
              </span>
            ) : (
              <span className="text-sm text-[var(--color-muted)] opacity-40">
                {t('captioning_no_signs')}
              </span>
            )}
          </div>
        </div>

        {/* Confidence bar */}
        {isRecording && confidence > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-[var(--color-muted)]">
              {t('captioning_confidence')}
            </span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-border)]" role="progressbar" aria-valuenow={confidencePercent} aria-valuemin={0} aria-valuemax={100} aria-label={`${t('captioning_confidence')}: ${confidencePercent}%`}>
              <motion.div
                className={cn(
                  'h-full rounded-full',
                  confidencePercent >= 80
                    ? 'bg-[var(--color-success)]'
                    : confidencePercent >= 50
                      ? 'bg-[var(--color-warning)]'
                      : 'bg-[var(--color-error)]'
                )}
                initial={{ width: 0 }}
                animate={{ width: `${confidencePercent}%` }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              />
            </div>
            <span className="text-xs font-mono text-[var(--color-muted)]">
              {confidencePercent}%
            </span>
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <p className="text-sm text-[var(--color-error)]" role="alert">
          {t('captioning_error')}
        </p>
      )}
    </div>
  )
}
