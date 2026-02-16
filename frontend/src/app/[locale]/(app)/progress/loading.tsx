import { Skeleton } from '@/components/shared/skeleton'

/**
 * Progress page loading skeleton.
 * Renders chart-like placeholders matching the progress dashboard layout.
 */
export default function Loading() {
  return (
    <div role="status" aria-label="Loading progress" className="max-w-6xl mx-auto space-y-8">
      <span className="sr-only">Loading progress...</span>

      {/* Header */}
      <Skeleton variant="text" className="w-48 h-7" />

      {/* Summary stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-3"
          >
            <Skeleton variant="text" className="w-20 h-4" />
            <Skeleton variant="text" className="w-16 h-8" />
          </div>
        ))}
      </div>

      {/* Chart placeholder */}
      <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
        <Skeleton variant="text" className="w-32 h-5 mb-4" />
        <Skeleton variant="rectangular" className="w-full h-48" />
      </div>
    </div>
  )
}
