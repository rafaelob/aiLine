'use client'

import { useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import Script from 'next/script'
import { cn } from '@/lib/cn'

/**
 * VLibras accessibility widget (ADR-010, ADR-032, FINDING-26).
 *
 * Loads the VLibras plugin from the government CDN via next/Script lazyOnload
 * to avoid impacting LCP.  The widget renders a floating accessibility button
 * that allows users to select text on the page for translation into Libras
 * (Brazilian Sign Language) through a 3D avatar.
 *
 * IMPORTANT: VLibras has NO programmatic `translate(text)` JS API.
 * Users must manually select text, and the widget translates it.
 * For server-side programmatic translation, use the VLibras Translator API.
 *
 * CDN: https://vlibras.gov.br/app/vlibras-plugin.js (v6.0.0, LGPLv3)
 */

const VLIBRAS_CDN = 'https://vlibras.gov.br/app/vlibras-plugin.js'
const SKIP_LINK_TARGET = 'vlibras-after'

interface VLibrasWidgetProps {
  /** Position of the floating widget button. */
  position?: 'left' | 'right'
  /** Additional CSS classes for the container. */
  className?: string
}

export function VLibrasWidget({
  position = 'right',
  className,
}: VLibrasWidgetProps) {
  const t = useTranslations('vlibras')
  const containerRef = useRef<HTMLDivElement>(null)
  const initializedRef = useRef(false)
  const [active, setActive] = useState(false)

  useEffect(() => {
    return () => {
      initializedRef.current = false
    }
  }, [])

  function handleScriptLoad() {
    if (initializedRef.current) return
    initializedRef.current = true
    setActive(true)

    // VLibras initializes itself when the script loads.
    // The `vw` global is created by the plugin and attaches to [vw]
    // elements on the page.  We trigger the widget initialization
    // after a short delay to ensure the DOM element is ready.
    const timer = setTimeout(() => {
      const vw = (window as unknown as Record<string, unknown>)['vw']
      if (vw && typeof (vw as Record<string, unknown>)['init'] === 'function') {
        ;(vw as { init: () => void }).init()
      }
    }, 200)

    return () => clearTimeout(timer)
  }

  return (
    <>
      {/* Skip-link: allows keyboard users to bypass the VLibras widget (FINDING-26) */}
      <a
        href={`#${SKIP_LINK_TARGET}`}
        className={cn(
          'sr-only focus:not-sr-only focus:absolute focus:z-50',
          'focus:rounded focus:bg-[var(--color-surface)] focus:px-3 focus:py-2',
          'focus:text-sm focus:text-[var(--color-text)] focus:shadow-lg',
        )}
      >
        {t('skip_widget')}
      </a>

      <div
        ref={containerRef}
        className={cn('vlibras-container', className)}
        aria-label={t('aria_label')}
        aria-hidden={!active}
        tabIndex={active ? undefined : -1}
      >
        {/* VLibras widget root element -- custom attributes via dangerouslySetInnerHTML
             because VLibras expects non-standard HTML attributes (vw, vw-access-button, etc.) */}
        <div
          dangerouslySetInnerHTML={{
            __html: `
              <div vw="true" class="enabled">
                <div vw-access-button="true" class="active" style="${position}: 10px" aria-label="${t('open_vlibras')}"></div>
                <div vw-plugin-wrapper="true">
                  <div class="vw-plugin-top-wrapper"></div>
                </div>
              </div>
            `,
          }}
        />

        <Script
          src={VLIBRAS_CDN}
          strategy="lazyOnload"
          onLoad={handleScriptLoad}
        />

        <p className="mt-2 text-xs text-[var(--color-muted)]">
          {t('help_text')}
        </p>
      </div>

      {/* Anchor target for the skip-link */}
      <div id={SKIP_LINK_TARGET} />
    </>
  )
}
