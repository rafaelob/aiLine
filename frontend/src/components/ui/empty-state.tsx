'use client'

import { cn } from '@/lib/cn'

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
  /** Primary CTA button/link. */
  action?: {
    label: string
    href: string
  }
  className?: string
}

/**
 * Reusable empty state for lists with no data.
 * Shows a centered illustration, title (text-balance), description, and CTA.
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 px-8',
        'rounded-[var(--radius-lg)] border border-dashed',
        'border-[var(--color-border)] bg-[var(--color-surface)]',
        className
      )}
    >
      <div
        className={cn(
          'flex items-center justify-center w-16 h-16',
          'rounded-full bg-[var(--color-surface-elevated)]'
        )}
        aria-hidden="true"
      >
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-[var(--color-text)] text-center text-balance">
        {title}
      </h3>
      <p className="text-sm text-[var(--color-muted)] text-center text-balance max-w-md">
        {description}
      </p>
      {action && (
        <a
          href={action.href}
          className={cn(
            'inline-flex items-center gap-2 px-5 py-2.5',
            'rounded-[var(--radius-md)]',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'text-sm font-medium',
            'hover:bg-[var(--color-primary-hover)]',
            'focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-[var(--color-primary)]',
            'transition-colors'
          )}
        >
          {action.label}
        </a>
      )}
    </div>
  )
}
