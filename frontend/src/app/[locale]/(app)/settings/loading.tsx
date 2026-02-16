export default function Loading() {
  return (
    <div className="max-w-3xl mx-auto space-y-6" aria-busy="true">
      <div className="animate-pulse glass rounded-2xl h-10 w-48" />
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="animate-pulse glass rounded-2xl h-32" />
      ))}
    </div>
  )
}
