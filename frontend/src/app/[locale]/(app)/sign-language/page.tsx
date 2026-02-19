'use client'

import { lazy, Suspense } from 'react'
import { useTranslations } from 'next-intl'
import { VLibrasWidget } from '@/components/sign-language/vlibras-widget'
import { GestureList } from '@/components/sign-language/gesture-list'
import { SkeletonCard } from '@/components/ui/skeleton'
import { PageTransition } from '@/components/ui/page-transition'

const WebcamCapture = lazy(() => import('@/components/sign-language/webcam-capture'))

/**
 * Sign language page -- combines continuous webcam gesture recognition
 * with real-time captioning, the VLibras accessibility widget,
 * and a supported gestures list.
 *
 * Continuous captioning flow:
 *   Webcam → rAF @20fps → MediaPipe landmarks → inference worker → WebSocket → LLM → caption
 */
export default function SignLanguagePage() {
  const t = useTranslations('sign_language')

  return (
    <PageTransition stagger>
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            {t('title')}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {t('subtitle')}
          </p>
        </div>

        {/* Webcam capture with integrated continuous captioning */}
        <section aria-label={t('webcam_section')}>
          <Suspense fallback={<SkeletonCard />}>
            <WebcamCapture />
          </Suspense>
        </section>

        {/* Supported gestures */}
        <section aria-label={t('supported_gestures')}>
          <GestureList />
        </section>

        {/* VLibras widget */}
        <section aria-label="VLibras">
          <h2 className="mb-3 text-lg font-semibold text-[var(--color-text)]">
            {t('vlibras_title')}
          </h2>
          <p className="mb-4 text-sm text-[var(--color-muted)]">
            {t('vlibras_description')}
          </p>
          <VLibrasWidget />
        </section>
      </div>
    </PageTransition>
  )
}
