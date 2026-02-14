export default function PlansLoading() {
  return (
    <div className="animate-pulse space-y-4 p-6" role="status" aria-label="Loading plans">
      <span className="sr-only">Loading plans...</span>
      <div className="h-8 w-48 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-40 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
        ))}
      </div>
    </div>
  )
}
