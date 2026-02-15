import { Skeleton } from '@/components/shared/skeleton'

/**
 * Plans page loading skeleton.
 * Renders a wizard-style skeleton with a header and 4 step indicators,
 * matching the plan creation wizard layout.
 */
export default function Loading() {
  return (
    <div role="status" aria-label="Loading plans" className="max-w-5xl mx-auto space-y-8">
      <span className="sr-only">Loading plans...</span>

      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton variant="text" className="w-40 h-7" />
        <Skeleton variant="rectangular" className="w-24 h-8" />
      </div>

      {/* Wizard step indicators */}
      <div className="flex items-center justify-center gap-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="flex flex-col items-center gap-1.5">
              <Skeleton
                variant="circular"
                className={i === 0 ? 'w-10 h-10' : 'w-8 h-8 opacity-60'}
              />
              <Skeleton variant="text" className="w-16 h-3" />
            </div>
            {i < 3 && (
              <Skeleton variant="text" className="w-12 h-0.5 opacity-30" />
            )}
          </div>
        ))}
      </div>

      {/* Wizard body skeleton */}
      <div
        className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 space-y-6"
      >
        {/* Form field skeletons */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Skeleton variant="text" className="w-24 h-4" />
            <Skeleton variant="rectangular" className="w-full h-10" />
          </div>
          <div className="space-y-2">
            <Skeleton variant="text" className="w-20 h-4" />
            <Skeleton variant="rectangular" className="w-full h-10" />
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-end gap-3 pt-4">
          <Skeleton variant="rectangular" className="w-20 h-10" />
          <Skeleton variant="rectangular" className="w-20 h-10" />
        </div>
      </div>
    </div>
  )
}
