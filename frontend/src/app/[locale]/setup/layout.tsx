import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AiLine Setup',
  description: 'Configure your AiLine instance',
}

/**
 * Minimal layout for the setup wizard.
 * No sidebar, no topbar -- clean centered container with branding.
 */
export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-3xl">{children}</div>
    </div>
  )
}
