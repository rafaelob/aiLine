import { getTranslations } from 'next-intl/server'
import { Sidebar } from '@/components/layout/sidebar'
import { TopBar } from '@/components/layout/topbar'
import { MobileNav } from '@/components/layout/mobile-nav'

interface AppLayoutProps {
  children: React.ReactNode
}

/**
 * App shell layout for authenticated pages.
 * Provides sidebar, topbar, and mobile navigation.
 * Used by all pages inside the (app) route group.
 */
export default async function AppLayout({ children }: AppLayoutProps) {
  const t = await getTranslations('common')

  return (
    <>
      {/* Skip navigation link for keyboard / screen reader users */}
      <a href="#main-content" className="skip-link">
        {t('skipToContent')}
      </a>

      <div className="flex h-screen overflow-hidden">
        {/* Sidebar navigation (hidden on mobile) */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Main content area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />

          <main
            id="main-content"
            className="flex-1 overflow-y-auto p-6 pb-20 md:pb-6"
          >
            {children}
          </main>
        </div>
      </div>

      {/* Mobile bottom navigation */}
      <MobileNav />
    </>
  )
}
