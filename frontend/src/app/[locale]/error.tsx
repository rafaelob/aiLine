'use client'
'use no memo'

import { useTranslations } from 'next-intl'
import { useParams } from 'next/navigation'
import { useEffect, useState, useCallback, useRef } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

/**
 * Global error boundary for the [locale] route group.
 *
 * Features:
 * - Branded accessible error page matching 9 persona themes (CSS vars)
 * - "Try again" button (calls Next.js reset to re-render the segment)
 * - "Reload page" button (hard reload fallback)
 * - "Copy diagnostic info" with request ID, timestamp, route, error digest
 * - SSE reconnect state: detects streaming errors and shows reconnect UI
 * - WCAG AAA: role="alert", aria-live, focus management, keyboard accessible
 */
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations('common')
  const params = useParams<{ locale: string }>()
  const [copied, setCopied] = useState(false)
  const [sseState, setSseState] = useState<'idle' | 'reconnecting' | 'failed'>('idle')
  const copiedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryButtonRef = useRef<HTMLButtonElement>(null)

  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const isSSEError =
    error.message?.includes('SSE') ||
    error.message?.includes('EventSource') ||
    error.message?.includes('stream') ||
    error.message?.includes('connection')

  useEffect(() => {
    console.error('[ErrorBoundary]', error)
  }, [error])

  // Focus the primary action button on mount for keyboard users
  useEffect(() => {
    retryButtonRef.current?.focus()
  }, [])

  // Clean up copied timeout on unmount to avoid setState on unmounted component
  useEffect(() => {
    return () => {
      if (copiedTimeoutRef.current) {
        clearTimeout(copiedTimeoutRef.current)
      }
    }
  }, [])

  // Build diagnostic info string
  const diagnosticInfo = useCallback(() => {
    const lines: string[] = [
      `${t('error_id')}: ${error.digest ?? 'N/A'}`,
      `${t('timestamp')}: ${new Date().toISOString()}`,
      `${t('route')}: ${typeof window !== 'undefined' ? window.location.pathname : 'N/A'}`,
      `Error: ${error.message ?? 'Unknown error'}`,
    ]
    if (error.stack) {
      lines.push(`\nStack:\n${error.stack.slice(0, 500)}`)
    }
    return lines.join('\n')
  }, [error, t])

  const handleCopyDiagnostics = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(diagnosticInfo())
      setCopied(true)
      if (copiedTimeoutRef.current) clearTimeout(copiedTimeoutRef.current)
      copiedTimeoutRef.current = setTimeout(() => setCopied(false), 2500)
    } catch {
      // Fallback for environments without clipboard API
      const textArea = document.createElement('textarea')
      textArea.value = diagnosticInfo()
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopied(true)
      if (copiedTimeoutRef.current) clearTimeout(copiedTimeoutRef.current)
      copiedTimeoutRef.current = setTimeout(() => setCopied(false), 2500)
    }
  }, [diagnosticInfo])

  const handleSSEReconnect = useCallback(() => {
    setSseState('reconnecting')
    // Attempt reconnect by calling reset after a brief delay
    setTimeout(() => {
      try {
        reset()
      } catch {
        setSseState('failed')
      }
    }, 1000)
  }, [reset])

  const handleReload = useCallback(() => {
    window.location.reload()
  }, [])

  return (
    <motion.div
      className="flex min-h-[60vh] items-center justify-center p-6"
      role="alert"
      aria-live="assertive"
      initial={noMotion ? undefined : { opacity: 0, y: 20, filter: 'blur(8px)' }}
      animate={noMotion ? undefined : { opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={noMotion ? undefined : { type: 'spring', stiffness: 200, damping: 24 }}
    >
      <div
        className={cn(
          'flex w-full max-w-lg flex-col items-center gap-6 text-center',
          'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
          'glass p-8',
          'shadow-[var(--shadow-lg)]',
        )}
      >
        {/* Error icon */}
        <div
          className="icon-orb flex h-16 w-16 items-center justify-center rounded-full"
          style={{ background: 'linear-gradient(135deg, var(--color-error), color-mix(in srgb, var(--color-error) 60%, var(--color-warning)))' }}
          aria-hidden="true"
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        {/* Title and description */}
        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-bold text-[var(--color-text)]">
            {t('error_title')}
          </h1>
          <p className="text-sm leading-relaxed text-[var(--color-muted)]">
            {t('error_description')}
          </p>
        </div>

        {/* SSE reconnect banner */}
        {isSSEError && (
          <div
            className={cn(
              'flex w-full items-center gap-3 rounded-[var(--radius-md)] px-4 py-3',
              'border text-sm glass',
              sseState === 'reconnecting'
                ? 'border-[var(--color-warning)]/30 text-[var(--color-text)]'
                : sseState === 'failed'
                  ? 'border-[var(--color-error)]/30 text-[var(--color-text)]'
                  : 'border-[var(--color-warning)]/30 text-[var(--color-text)]',
            )}
            role="status"
            aria-live="polite"
          >
            {sseState === 'reconnecting' ? (
              <>
                <ReconnectSpinner />
                <span>{t('sse_reconnecting')}</span>
              </>
            ) : sseState === 'failed' ? (
              <>
                <span className="flex-1">{t('sse_reconnect_failed')}</span>
                <button
                  onClick={handleSSEReconnect}
                  className={cn(
                    'shrink-0 rounded-[var(--radius-md)] px-3 py-1.5',
                    'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                    'text-xs font-semibold',
                    'hover:bg-[var(--color-primary-hover)]',
                    'focus-visible:outline-2 focus-visible:outline-offset-2',
                    'focus-visible:outline-[var(--color-primary)]',
                    'transition-colors',
                  )}
                >
                  {t('sse_reconnect')}
                </button>
              </>
            ) : (
              <>
                <span className="flex-1">{t('sse_reconnecting').split('.')[0]}.</span>
                <button
                  onClick={handleSSEReconnect}
                  className={cn(
                    'shrink-0 rounded-[var(--radius-md)] px-3 py-1.5',
                    'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                    'text-xs font-semibold',
                    'hover:bg-[var(--color-primary-hover)]',
                    'focus-visible:outline-2 focus-visible:outline-offset-2',
                    'focus-visible:outline-[var(--color-primary)]',
                    'transition-colors',
                  )}
                >
                  {t('sse_reconnect')}
                </button>
              </>
            )}
          </div>
        )}

        {/* Diagnostic info (collapsible) */}
        <div className="flex w-full flex-col gap-2">
          {error.digest && (
            <p className="font-mono text-xs text-[var(--color-muted)]">
              {t('error_id')}: {error.digest}
            </p>
          )}

          <button
            onClick={handleCopyDiagnostics}
            className={cn(
              'flex w-full items-center justify-center gap-2',
              'rounded-[var(--radius-md)] border border-[var(--color-border)]',
              'px-4 py-2 text-xs font-medium',
              'text-[var(--color-muted)]',
              'hover:glass hover:bg-[var(--color-surface-elevated)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'transition-colors',
            )}
            aria-label={t('copy_diagnostics')}
          >
            {copied ? (
              <>
                <CheckIcon />
                <span>{t('diagnostics_copied')}</span>
              </>
            ) : (
              <>
                <ClipboardIcon />
                <span>{t('copy_diagnostics')}</span>
              </>
            )}
          </button>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            ref={retryButtonRef}
            onClick={reset}
            className={cn(
              'rounded-[var(--radius-md)] px-5 py-2.5',
              'text-[var(--color-on-primary)]',
              'text-sm font-semibold',
              'btn-shimmer',
              'hover:brightness-110',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'transition-all',
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            {t('retry')}
          </button>

          <button
            onClick={handleReload}
            className={cn(
              'rounded-[var(--radius-md)] px-5 py-2.5',
              'border border-[var(--color-border)]',
              'text-sm font-semibold text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'transition-colors',
            )}
          >
            {t('reload')}
          </button>

          <a
            href={`/${params.locale ?? 'en'}`}
            className={cn(
              'rounded-[var(--radius-md)] px-5 py-2.5',
              'border border-[var(--color-border)]',
              'text-sm font-semibold text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'transition-colors',
            )}
          >
            {t('go_home')}
          </a>
        </div>
      </div>
    </motion.div>
  )
}

/* --- Icons --- */

function ClipboardIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="9" y="2" width="6" height="4" rx="1" />
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function ReconnectSpinner() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="animate-spin"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
}
