'use client'

import { useEffect, useState } from 'react'
import { useTranslations, useLocale } from 'next-intl'
import { cn } from '@/lib/cn'
import type { GestureInfo, GestureListResponse } from '@/types/sign-language'

/**
 * Displays the list of supported Libras gestures (ADR-026).
 *
 * Fetches from GET /sign-language/gestures and renders a card grid
 * with gesture name in the current locale and the canonical ID.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

interface GestureListProps {
  className?: string
}

/** Map locale to the gesture name field. */
function getGestureName(gesture: GestureInfo, locale: string): string {
  if (locale === 'pt-BR') return gesture.name_pt
  if (locale === 'es') return gesture.name_es
  return gesture.name_en
}

export function GestureList({ className }: GestureListProps) {
  const t = useTranslations('sign_language')
  const locale = useLocale()

  const [gestures, setGestures] = useState<GestureInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function fetchGestures() {
      try {
        const response = await fetch(`${API_BASE}/sign-language/gestures`)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data: GestureListResponse = await response.json()
        if (!cancelled) {
          setGestures(data.gestures)
          setLoading(false)
        }
      } catch {
        if (!cancelled) {
          setError(true)
          setLoading(false)
        }
      }
    }

    fetchGestures()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center py-8', className)}>
        <p className="text-sm text-[var(--color-muted)]">{t('loading_gestures')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center py-8', className)} role="alert">
        <p className="text-sm text-[var(--color-error)]">{t('error_loading_gestures')}</p>
      </div>
    )
  }

  return (
    <div className={className}>
      <h3 className="mb-4 text-lg font-semibold text-[var(--color-text)]">
        {t('supported_gestures')}
      </h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {gestures.map((gesture) => (
          <div
            key={gesture.id}
            className={cn(
              'flex flex-col items-center gap-2 rounded-[var(--radius-md)] p-4',
              'border border-[var(--color-border)] bg-[var(--color-surface-elevated)]',
              'transition-colors hover:border-[var(--color-primary)]'
            )}
          >
            <span className="text-3xl" aria-hidden="true">
              {gestureEmoji(gesture.id)}
            </span>
            <span className="text-sm font-medium text-[var(--color-text)]">
              {getGestureName(gesture, locale)}
            </span>
            <span className="text-xs text-[var(--color-muted)]">
              {gesture.id}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-[var(--color-muted)]">
        {t('gestures_note')}
      </p>
    </div>
  )
}

/** Map gesture ID to a representative emoji for visual identification. */
function gestureEmoji(id: string): string {
  const map: Record<string, string> = {
    oi: '\u{1F44B}',       // waving hand
    obrigado: '\u{1F64F}', // folded hands
    sim: '\u{1F44D}',      // thumbs up
    nao: '\u{1F44E}',      // thumbs down
  }
  return map[id] ?? '\u{270B}'  // raised hand fallback
}
