import { Skeleton } from '@/components/shared/skeleton'

/**
 * Tutors page loading skeleton.
 * Renders a chat-style skeleton with a header area and message bubbles,
 * matching the tutor chat interface layout.
 */
export default function Loading() {
  return (
    <div role="status" aria-label="Loading tutor" className="max-w-4xl mx-auto space-y-4">
      <span className="sr-only">Loading tutor...</span>

      {/* Header skeleton */}
      <div className="space-y-1">
        <Skeleton variant="text" className="w-32 h-7" />
        <Skeleton variant="text" className="w-64 h-4" />
      </div>

      {/* Chat area skeleton */}
      <div
        className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] flex flex-col"
        style={{ minHeight: '480px' }}
      >
        {/* Tab bar skeleton */}
        <div className="flex gap-2 p-3 border-b border-[var(--color-border)]">
          <Skeleton variant="rectangular" className="w-16 h-8" />
          <Skeleton variant="rectangular" className="w-16 h-8" />
        </div>

        {/* Message area */}
        <div className="flex-1 p-4 space-y-4">
          {/* Welcome message skeleton */}
          <div className="flex flex-col items-center justify-center py-8 space-y-3">
            <Skeleton variant="circular" className="w-16 h-16" />
            <Skeleton variant="text" className="w-48 h-5" />
            <Skeleton variant="text" className="w-72 h-4" />
          </div>

          {/* Example prompt suggestions */}
          <div className="flex flex-wrap justify-center gap-2">
            <Skeleton variant="rectangular" className="w-40 h-9 rounded-full" />
            <Skeleton variant="rectangular" className="w-36 h-9 rounded-full" />
            <Skeleton variant="rectangular" className="w-44 h-9 rounded-full" />
          </div>
        </div>

        {/* Input area skeleton */}
        <div className="p-3 border-t border-[var(--color-border)] flex items-center gap-2">
          <Skeleton variant="rectangular" className="flex-1 h-10 rounded-full" />
          <Skeleton variant="circular" className="w-10 h-10" />
        </div>
      </div>
    </div>
  )
}
