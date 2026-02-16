export default function ObservabilityLoading() {
  return (
    <div className="animate-pulse space-y-4 p-6" role="status" aria-label="Loading observability">
      <span className="sr-only">Loading observability dashboard...</span>
      <div className="h-8 w-52 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="h-32 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
        ))}
      </div>
    </div>
  )
}
