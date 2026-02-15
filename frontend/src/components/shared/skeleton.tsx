import { cn } from '@/lib/cn'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
}

/**
 * Animated loading skeleton placeholder.
 */
export function Skeleton({ className, variant = 'text', width, height }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-[var(--color-surface-elevated)]',
        variant === 'text' && 'h-4 rounded-[var(--radius-sm)]',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-[var(--radius-md)]',
        className
      )}
      style={{ width, height }}
      role="status"
      aria-label="Loading..."
    />
  )
}

/**
 * Card-shaped skeleton for loading states.
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-6 space-y-4',
        className
      )}
    >
      <Skeleton variant="text" className="w-3/4 h-5" />
      <Skeleton variant="text" className="w-1/2 h-4" />
      <div className="flex gap-2 pt-2">
        <Skeleton variant="rectangular" className="w-16 h-6" />
        <Skeleton variant="rectangular" className="w-20 h-6" />
      </div>
    </div>
  )
}
