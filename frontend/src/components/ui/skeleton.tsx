'use client'

import { cn } from '@/lib/cn'

interface SkeletonProps {
  className?: string
  /** Number of skeleton lines to render */
  lines?: number
}

/**
 * Shimmer skeleton component for loading states.
 * Uses CSS animation from globals.css `.skeleton` class.
 */
export function Skeleton({ className, lines = 1 }: SkeletonProps) {
  if (lines > 1) {
    return (
      <div className="space-y-3" aria-hidden="true">
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className={cn(
              'skeleton h-4',
              i === lines - 1 && 'w-3/4',
              className
            )}
          />
        ))}
      </div>
    )
  }

  return <div className={cn('skeleton h-4', className)} aria-hidden="true" />
}

/**
 * Card-shaped skeleton for loading dashboard cards.
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-5 space-y-4',
        className
      )}
      aria-hidden="true"
    >
      <div className="flex items-center gap-4">
        <div className="skeleton h-12 w-12 rounded-[var(--radius-md)]" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-4 w-1/2" />
          <div className="skeleton h-3 w-1/3" />
        </div>
      </div>
      <Skeleton lines={3} />
    </div>
  )
}
