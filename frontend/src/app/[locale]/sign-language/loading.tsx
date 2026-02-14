export default function SignLanguageLoading() {
  return (
    <div className="animate-pulse space-y-4 p-6" role="status" aria-label="Loading sign language">
      <span className="sr-only">Loading sign language...</span>
      <div className="h-8 w-56 rounded bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      <div className="grid gap-6 md:grid-cols-2">
        <div className="aspect-video rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
        <div className="aspect-video rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
      </div>
      <div className="h-24 rounded-xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
    </div>
  )
}
