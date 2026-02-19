'use client'

import { cn } from '@/lib/cn'

interface LandingFooterProps {
  builtWith: string
  openSource: string
  createdWith: string
  hackathon: string
}

/**
 * Footer with prominent "Built with Claude Opus 4.6" badge and copyright.
 */
export function LandingFooter({ builtWith, openSource, createdWith, hackathon }: LandingFooterProps) {
  return (
    <footer
      role="contentinfo"
      className={cn(
        'py-10 px-6 mt-auto',
        'border-t border-[var(--color-border)]',
        'flex flex-col items-center gap-4'
      )}
    >
      {/* Badges row */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {/* Built with Opus badge */}
        <div
          className={cn(
            'inline-flex items-center gap-3 px-5 py-2.5',
            'rounded-full',
            'border border-[var(--color-border)]',
            'bg-[var(--color-surface)]',
            'badge-glow'
          )}
        >
          <div
            className="w-7 h-7 rounded-lg shrink-0"
            style={{
              background: 'linear-gradient(135deg, #CC785C, #D4A574)',
              boxShadow: '0 0 12px rgba(204, 120, 92, 0.4)',
            }}
            aria-hidden="true"
          />
          <span className="text-sm font-semibold text-[var(--color-text)]">
            {builtWith}
          </span>
        </div>

        {/* Open Source badge */}
        <div
          className={cn(
            'inline-flex items-center gap-2 px-4 py-2',
            'rounded-full',
            'border border-[var(--color-border)]',
            'bg-[var(--color-surface)]'
          )}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--color-muted)]" aria-hidden="true">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          <span className="text-xs font-medium text-[var(--color-muted)]">
            {openSource}
          </span>
        </div>

        {/* GitHub icon badge */}
        <div
          className={cn(
            'inline-flex items-center gap-2 px-4 py-2',
            'rounded-full',
            'border border-[var(--color-border)]',
            'bg-[var(--color-surface)]'
          )}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-[var(--color-muted)]" aria-hidden="true">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          <span className="text-xs font-medium text-[var(--color-muted)]">
            {createdWith}
          </span>
        </div>
      </div>

      {/* Hackathon line */}
      <p className="text-xs font-medium text-[var(--color-muted)]">
        {hackathon}
      </p>

      {/* Copyright */}
      <p className="text-xs text-[var(--color-muted)]">
        &copy; {new Date().getFullYear()} AiLine &mdash; Adaptive Inclusive Learning
      </p>
    </footer>
  )
}
