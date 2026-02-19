/**
 * Reusable SVG icon component for login role cards.
 * Takes a raw SVG path string and renders an accessible icon.
 */
export function RoleIcon({ path, className }: { path: string; className?: string }) {
  return (
    <svg
      className={className}
      width="28"
      height="28"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  )
}
