'use client'

import { useTranslations } from 'next-intl'
import { useEffect } from 'react'
import { cn } from '@/lib/cn'

/**
 * Global error boundary for the [locale] route group.
 * Catches unhandled errors and displays a user-friendly page
 * with retry and go-home options. Supports all 9 persona themes
 * via CSS custom properties.
 */
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations('common')

  useEffect(() => {
    // Log error for debugging (production: send to observability)
    console.error('[ErrorBoundary]', error)
  }, [error])

  return (
    <div
      className="flex min-h-[60vh] items-center justify-center p-6"
      role="alert"
      aria-live="assertive"
    >
      <div
        className={cn(
          'flex max-w-md flex-col items-center gap-6 text-center',
          'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
          'bg-[var(--color-surface)] p-8',
          'shadow-[var(--shadow-lg)]',
        )}
      >
        {/* Error icon */}
        <div
          className={cn(
            'flex h-16 w-16 items-center justify-center rounded-full',
            'bg-[var(--color-error)]/10',
          )}
          aria-hidden="true"
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-error)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-bold text-[var(--color-text)]">
            {t('error_title')}
          </h1>
          <p className="text-sm leading-relaxed text-[var(--color-muted)]">
            {t('error_description')}
          </p>
        </div>

        {error.digest && (
          <p className="font-mono text-xs text-[var(--color-muted)]">
            {error.digest}
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={reset}
            className={cn(
              'rounded-[var(--radius-md)] px-5 py-2.5',
              'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
              'text-sm font-semibold',
              'hover:bg-[var(--color-primary-hover)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'transition-colors',
            )}
          >
            {t('retry')}
          </button>

          {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- Error boundaries must use <a> to work when the router is broken */}
          <a
            href="/"
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
    </div>
  )
}
