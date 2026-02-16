import { Skeleton, SkeletonCard } from '@/components/shared/skeleton'

/**
 * Dashboard root loading skeleton.
 * Renders a grid of 6 skeleton cards (2 rows of 3) matching the dashboard layout:
 * hero section, stat cards row, and quick action / recent plans grid.
 */
export default function Loading() {
  return (
    <div role="status" aria-label="Loading dashboard" className="space-y-6 animate-in fade-in">
      <span className="sr-only">Loading dashboard...</span>

      {/* Hero skeleton */}
      <div className="rounded-2xl bg-[var(--color-surface)] p-8 md:p-10 space-y-3">
        <Skeleton variant="text" className="w-1/3 h-7" />
        <Skeleton variant="text" className="w-1/2 h-4" />
      </div>

      {/* Stats row skeleton (3 cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Recent plans skeleton (3 cards) */}
      <div className="space-y-3">
        <Skeleton variant="text" className="w-32 h-4" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  )
}
