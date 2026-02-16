'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'

/**
 * PWA install prompt banner.
 *
 * Listens for the `beforeinstallprompt` event and shows a dismissible
 * banner inviting the user to install the app. Remembers dismissal
 * in localStorage for 30 days.
 */
export function InstallPrompt() {
  const t = useTranslations('pwa')
  const [showPrompt, setShowPrompt] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const deferredPromptRef = useRef<any>(null)

  useEffect(() => {
    // Check if user dismissed recently
    const dismissed = localStorage.getItem('ailine-pwa-dismissed')
    if (dismissed) {
      const dismissedAt = Number(dismissed)
      const thirtyDays = 30 * 24 * 60 * 60 * 1000
      if (Date.now() - dismissedAt < thirtyDays) return
    }

    const handler = (e: Event) => {
      e.preventDefault()
      deferredPromptRef.current = e
      setShowPrompt(true)
    }

    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = useCallback(async () => {
    if (!deferredPromptRef.current) return

    await deferredPromptRef.current.prompt()
    deferredPromptRef.current = null
    setShowPrompt(false)
  }, [])

  const handleDismiss = useCallback(() => {
    localStorage.setItem('ailine-pwa-dismissed', String(Date.now()))
    setShowPrompt(false)
  }, [])

  if (!showPrompt) return null

  return (
    <div
      role="banner"
      aria-label={t('install_label')}
      className="fixed bottom-4 left-4 right-4 z-50 flex items-center justify-between
                 rounded-lg bg-[var(--color-primary)] p-4 text-white shadow-lg
                 md:left-4 md:right-auto md:w-96"
    >
      <div className="flex-1">
        <p className="text-sm font-medium">{t('install_title')}</p>
        <p className="text-xs opacity-80">
          {t('install_description')}
        </p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleDismiss}
          className="rounded px-3 py-1.5 text-xs font-medium opacity-80 hover:opacity-100
                     focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          aria-label={t('dismiss_label')}
        >
          {t('later')}
        </button>
        <button
          onClick={handleInstall}
          className="rounded bg-white px-3 py-1.5 text-xs font-medium text-[var(--color-primary)]
                     hover:bg-opacity-90
                     focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          aria-label={t('install_label')}
        >
          {t('install')}
        </button>
      </div>
    </div>
  )
}
