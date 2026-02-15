import type { Metadata } from 'next'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages, getTranslations } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import { Sidebar } from '@/components/layout/sidebar'
import { TopBar } from '@/components/layout/topbar'
import { MobileNav } from '@/components/layout/mobile-nav'
import { A11yHydrator } from '@/components/accessibility/a11y-hydrator'
import { CognitiveCurtain } from '@/components/accessibility/cognitive-curtain'
import { RouteAnnouncer } from '@/components/accessibility/route-announcer'
import { ServiceWorkerRegistrar } from '@/components/pwa/sw-registrar'
import { InstallPrompt } from '@/components/pwa/install-prompt'
import { ToastProvider } from '@/components/ui/toast-provider'
import { DemoTooltip } from '@/components/shared/demo-tooltip'
import { CommandPalette } from '@/components/shared/command-palette'
import '@/styles/globals.css'

/**
 * Blocking script that applies the persisted theme before React hydrates,
 * preventing a flash of the wrong theme (FOUC).
 */
function ThemeScript() {
  const code = `(function(){try{var s=localStorage.getItem('ailine-a11y-prefs');if(s){var p=JSON.parse(s);var t=p.theme||'standard';document.documentElement.setAttribute('data-theme',t);document.body&&document.body.setAttribute('data-theme',t);if(p.reducedMotion){document.body&&document.body.setAttribute('data-reduced-motion','true')}}}catch(e){}})()`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}

interface LocaleLayoutProps {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

/**
 * Generate locale-aware metadata using Next.js Metadata API.
 */
export async function generateMetadata({
  params,
}: LocaleLayoutProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'app' })
  const tLanding = await getTranslations({ locale, namespace: 'landing' })

  const title = `${t('name')} - ${t('tagline')}`
  const description = tLanding('hero_subtitle')

  return {
    title: {
      default: title,
      template: `%s | ${t('name')}`,
    },
    description,
    applicationName: t('name'),
    openGraph: {
      type: 'website',
      title,
      description,
      siteName: t('name'),
      images: [
        {
          url: '/api/og?title=AiLine&subtitle=Adaptive+Inclusive+Learning',
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: ['/api/og?title=AiLine&subtitle=Adaptive+Inclusive+Learning'],
    },
    manifest: '/manifest.json',
    appleWebApp: {
      capable: true,
      statusBarStyle: 'default',
      title: t('name'),
    },
    other: {
      'theme-color': '#2563EB',
    },
  }
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
  const t = await getTranslations('common')

  return (
    <html lang={locale}>
      <head>
        <ThemeScript />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.svg" />
      </head>
      <body data-theme="standard" className="antialiased bg-[var(--color-bg)]" suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <A11yHydrator />
          <CognitiveCurtain />
          <RouteAnnouncer />
          <ServiceWorkerRegistrar />

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
          <DemoTooltip />
          <CommandPalette />
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
