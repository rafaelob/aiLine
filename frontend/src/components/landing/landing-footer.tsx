'use client'

import { cn } from '@/lib/cn'

interface LandingFooterProps {
  builtWith: string
}

/**
 * Footer with prominent "Built with Claude Opus 4.6" badge and copyright.
 */
export function LandingFooter({ builtWith }: LandingFooterProps) {
  return (
    <footer
      className={cn(
        'py-10 px-6 mt-auto',
        'border-t border-[var(--color-border)]',
        'flex flex-col items-center gap-4'
      )}
    >
      {/* Badge */}
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

      {/* Copyright */}
      <p className="text-xs text-[var(--color-muted)]">
        &copy; {new Date().getFullYear()} AiLine &mdash; Adaptive Inclusive Learning
      </p>
    </footer>
  )
}
