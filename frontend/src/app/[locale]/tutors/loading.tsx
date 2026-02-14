export default function TutorsLoading() {
  return (
    <div className="animate-pulse space-y-4 p-6" role="status" aria-label="Loading tutor">
      <span className="sr-only">Loading tutor...</span>
      <div className="h-8 w-40 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="h-6 w-64 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="mt-4 space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-16 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
        ))}
      </div>
      <div className="h-12 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
    </div>
  )
}
