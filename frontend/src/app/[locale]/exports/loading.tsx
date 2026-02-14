export default function ExportsLoading() {
  return (
    <div className="animate-pulse space-y-4 p-6" role="status" aria-label="Loading exports">
      <span className="sr-only">Loading exports...</span>
      <div className="h-8 w-44 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="flex gap-6">
        <div className="w-64 shrink-0 space-y-2">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-12 rounded-lg bg-[var(--color-surface-elevated)]" aria-hidden="true" />
          ))}
        </div>
        <div className="flex-1 h-80 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      </div>
    </div>
  )
}
