'use client'

import { useTranslations } from 'next-intl'
import { useEffect } from 'react'

/**
 * Global error boundary for the [locale] route group.
 * Catches unhandled errors and displays a user-friendly page
 * with retry and go-home options.
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
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div
        className="glass flex max-w-md flex-col items-center gap-6 rounded-2xl p-8 text-center"
        style={{
          boxShadow: 'var(--shadow-lg)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        {/* Error icon */}
        <div
          className="flex h-16 w-16 items-center justify-center rounded-full"
          style={{ background: 'var(--color-error)', color: 'var(--color-on-primary)' }}
          aria-hidden="true"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <h1
          className="text-2xl font-bold"
          style={{ color: 'var(--color-text)' }}
        >
          {t('error_title')}
        </h1>

        <p
          className="text-base leading-relaxed"
          style={{ color: 'var(--color-muted)' }}
        >
          {t('error_description')}
        </p>

        {error.digest && (
          <p
            className="font-mono text-xs"
            style={{ color: 'var(--color-muted)' }}
          >
            {error.digest}
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={reset}
            className="rounded-lg px-6 py-3 text-sm font-semibold transition-shadow hover:shadow-md focus-visible:outline focus-visible:outline-2"
            style={{
              background: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              borderRadius: 'var(--radius-md)',
              outlineColor: 'var(--focus-ring)',
            }}
          >
            {t('retry')}
          </button>

          {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- Error boundaries must use <a> to work when the router is broken */}
          <a
            href="/"
            className="rounded-lg border px-6 py-3 text-sm font-semibold transition-shadow hover:shadow-md focus-visible:outline focus-visible:outline-2"
            style={{
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              borderRadius: 'var(--radius-md)',
              outlineColor: 'var(--focus-ring)',
            }}
          >
            {t('go_home')}
          </a>
        </div>
      </div>
    </div>
  )
}
