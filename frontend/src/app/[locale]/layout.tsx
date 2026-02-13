import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import { Sidebar } from '@/components/layout/sidebar'
import { TopBar } from '@/components/layout/topbar'
import { MobileNav } from '@/components/layout/mobile-nav'
import { A11yHydrator } from '@/components/accessibility/a11y-hydrator'
import { ServiceWorkerRegistrar } from '@/components/pwa/sw-registrar'
import { InstallPrompt } from '@/components/pwa/install-prompt'
import { ToastProvider } from '@/components/ui/toast-provider'
import '@/styles/globals.css'

interface LocaleLayoutProps {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

/**
 * Root layout with next-intl provider, sidebar, topbar, and mobile nav.
 * Locale extracted from dynamic route segment.
 * params must be awaited (Next.js 16 requirement).
 */
export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
  const { locale } = await params

  if (!routing.locales.includes(locale as typeof routing.locales[number])) {
    notFound()
  }

  const messages = await getMessages()

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <title>AiLine - Adaptive Inclusive Learning</title>
        <meta
          name="description"
          content="AI-powered inclusive education platform for adaptive learning"
        />
        {/* Open Graph / Social preview */}
        <meta property="og:type" content="website" />
        <meta property="og:title" content="AiLine - Adaptive Inclusive Learning" />
        <meta
          property="og:description"
          content="AI-powered inclusive education platform for adaptive learning"
        />
        <meta property="og:image" content="/api/og?title=AiLine&subtitle=Adaptive+Inclusive+Learning" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="AiLine - Adaptive Inclusive Learning" />
        <meta name="twitter:image" content="/api/og?title=AiLine&subtitle=Adaptive+Inclusive+Learning" />
        {/* PWA meta tags */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#2563EB" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="AiLine" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.svg" />
      </head>
      <body data-theme="standard" className="antialiased">
        <NextIntlClientProvider messages={messages}>
          <A11yHydrator />
          <ServiceWorkerRegistrar />

          {/* Skip navigation link for keyboard / screen reader users */}
          <a href="#main-content" className="skip-link">
            Skip to main content
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
                role="main"
                className="flex-1 overflow-y-auto p-6 pb-20 md:pb-6"
              >
                {children}
              </main>
            </div>
          </div>

          {/* Mobile bottom navigation */}
          <MobileNav />
          <InstallPrompt />
          <ToastProvider />
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
