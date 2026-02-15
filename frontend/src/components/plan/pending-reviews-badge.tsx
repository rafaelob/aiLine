'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface PendingReview {
  review_id: string
  plan_id: string
  teacher_id: string
  status: string
  notes: string
  approved_at: string | null
  created_at: string
}

export function PendingReviewsBadge() {
  const t = useTranslations('review')
  const [reviews, setReviews] = useState<PendingReview[]>([])
  const [expanded, setExpanded] = useState(false)
  const [loaded, setLoaded] = useState(false)

  const fetchPending = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/plans/pending-review`, {
        headers: getAuthHeaders(),
      })
      if (!res.ok) return
      const data: PendingReview[] = await res.json()
      setReviews(data)
    } catch {
      // Silent fail for MVP
    } finally {
      setLoaded(true)
    }
  }, [])

  useEffect(() => {
    fetchPending()
  }, [fetchPending])

  if (!loaded || reviews.length === 0) return null

  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-warning)]/30',
        'bg-[var(--color-warning)]/5 overflow-hidden',
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className={cn(
          'w-full flex items-center justify-between px-5 py-3',
          'hover:bg-[var(--color-warning)]/10 transition-colors',
        )}
      >
        <div className="flex items-center gap-3">
          <span
            className={cn(
              'inline-flex items-center justify-center w-6 h-6 rounded-full',
              'bg-[var(--color-warning)] text-white text-xs font-bold',
            )}
          >
            {reviews.length}
          </span>
          <span className="text-sm font-medium text-[var(--color-text)]">
            {t('pending')}
          </span>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="var(--color-muted)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          className={cn('transition-transform', expanded && 'rotate-180')}
        >
          <path d="M4 6l4 4 4-4" />
        </svg>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <ul className="divide-y divide-[var(--color-border)] px-5 pb-3">
              {reviews.map((r) => (
                <li key={r.review_id} className="py-2.5 flex items-center justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--color-text)] truncate">
                      {r.plan_id}
                    </p>
                    <p className="text-xs text-[var(--color-muted)]">
                      {new Date(r.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold uppercase',
                      'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
                    )}
                  >
                    {t('pending')}
                  </span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
