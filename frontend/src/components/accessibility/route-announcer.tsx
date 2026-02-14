'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useRef } from 'react'
import { useTranslations } from 'next-intl'

/**
 * Announces route changes to screen readers via aria-live region.
 * On navigation, reads the new page's h1 and moves focus to main content.
 * Uses i18n for the announcement text.
 */
export function RouteAnnouncer() {
  const pathname = usePathname()
  const announcerRef = useRef<HTMLDivElement>(null)
  const t = useTranslations('common')

  useEffect(() => {
    const h1 = document.querySelector('h1')
    const pageTitle = h1?.textContent || 'AiLine'

    if (announcerRef.current) {
      announcerRef.current.textContent = t('navigated_to', { page: pageTitle })
    }

    const main = document.getElementById('main-content')
    if (main) {
      main.setAttribute('tabindex', '-1')
      main.focus({ preventScroll: false })
    }
  }, [pathname, t])

  return (
    <div
      ref={announcerRef}
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="sr-only"
    />
  )
}
