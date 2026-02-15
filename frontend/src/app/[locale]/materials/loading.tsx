export default function MaterialsLoading() {
  return (
    <div className="max-w-5xl mx-auto space-y-6" role="status" aria-label="Loading materials">
      <span className="sr-only">Loading materials...</span>
      <div className="animate-pulse h-12 w-64 rounded-2xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="animate-pulse h-32 rounded-2xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
        ))}
      </div>
    </div>
  )
}
