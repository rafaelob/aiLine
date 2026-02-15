'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface ReviewData {
  review_id: string
  plan_id: string
  teacher_id: string
  status: string
  notes: string
  approved_at: string | null
  created_at: string
}

interface TeacherReviewPanelProps {
  planId: string
  initialReview?: ReviewData | null
  onReviewSubmitted?: (review: ReviewData) => void
  className?: string
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'var(--color-muted)',
  pending_review: 'var(--color-warning)',
  approved: 'var(--color-success)',
  rejected: 'var(--color-error)',
  needs_revision: 'var(--color-warning)',
}

export function TeacherReviewPanel({
  planId,
  initialReview,
  onReviewSubmitted,
  className,
}: TeacherReviewPanelProps) {
  const t = useTranslations('review')
  const [review, setReview] = useState<ReviewData | null>(initialReview ?? null)
  const [notes, setNotes] = useState(initialReview?.notes ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submitReview = useCallback(
    async (status: string) => {
      setSubmitting(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/plans/${planId}/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
          body: JSON.stringify({ status, notes }),
        })
        if (!res.ok) throw new Error(`Failed: ${res.status}`)
        const data: ReviewData = await res.json()
        setReview(data)
        onReviewSubmitted?.(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to submit review')
      } finally {
        setSubmitting(false)
      }
    },
    [planId, notes, onReviewSubmitted],
  )

  const currentStatus = review?.status ?? 'pending_review'
  const isFinalized = currentStatus === 'approved' || currentStatus === 'rejected'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] overflow-hidden',
        className,
      )}
    >
      {/* Header with status badge */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <ReviewIcon />
          <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('title')}</h3>
        </div>
        <StatusBadge status={currentStatus} label={t(currentStatus === 'pending_review' ? 'pending' : currentStatus)} />
      </div>

      {/* Review form / finalized view */}
      <div className="p-6 space-y-4">
        {!isFinalized && (
          <>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t('notes_placeholder')}
              rows={3}
              maxLength={2000}
              aria-label={t('notes_placeholder')}
              className={cn(
                'w-full rounded-[var(--radius-md)] border border-[var(--color-border)]',
                'bg-[var(--color-bg)] p-3 text-sm text-[var(--color-text)]',
                'placeholder:text-[var(--color-muted)] resize-y',
              )}
            />

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => submitReview('approved')}
                disabled={submitting}
                className={cn(
                  'px-5 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
                  'bg-[var(--color-success)] text-white',
                  'hover:opacity-90 transition-opacity',
                  'disabled:opacity-50',
                )}
              >
                {t('approve')}
              </button>
              <button
                type="button"
                onClick={() => submitReview('needs_revision')}
                disabled={submitting}
                className={cn(
                  'px-5 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
                  'border border-[var(--color-warning)] text-[var(--color-warning)]',
                  'hover:bg-[var(--color-warning)]/5 transition-colors',
                  'disabled:opacity-50',
                )}
              >
                {t('request_revision')}
              </button>
              <button
                type="button"
                onClick={() => submitReview('rejected')}
                disabled={submitting}
                className={cn(
                  'px-5 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
                  'border border-[var(--color-error)] text-[var(--color-error)]',
                  'hover:bg-[var(--color-error)]/5 transition-colors',
                  'disabled:opacity-50',
                )}
              >
                {t('reject')}
              </button>
            </div>
          </>
        )}

        {isFinalized && review && (
          <div className="space-y-2">
            {review.notes && (
              <p className="text-sm text-[var(--color-text)]">{review.notes}</p>
            )}
            {review.approved_at && (
              <p className="text-xs text-[var(--color-muted)]">
                {new Date(review.approved_at).toLocaleString()}
              </p>
            )}
          </div>
        )}

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="text-xs text-[var(--color-error)]"
              role="alert"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

function StatusBadge({ status, label }: { status: string; label: string }) {
  const color = STATUS_COLORS[status] ?? 'var(--color-muted)'
  return (
    <span
      className="inline-flex px-3 py-1 rounded-full text-xs font-bold uppercase"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
        color,
      }}
    >
      {label}
    </span>
  )
}

function ReviewIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--color-primary)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  )
}
