import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Login',
  description: 'Sign in to AiLine - Adaptive Inclusive Learning',
}

/**
 * Login layout — clean full-screen, no sidebar/topbar.
 * Similar to the setup wizard layout.
 */
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      {children}
    </div>
  )
}
