'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { EmptyState } from '@/components/shared/empty-state'
import { SkeletonCard } from '@/components/shared/skeleton'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface Flag {
  flag_id: string
  session_id: string
  turn_index: number
  teacher_id: string
  reason: string
  created_at: string
}

interface TranscriptData {
  session_id: string
  tutor_id: string
  messages: Message[]
  flags: Flag[]
  created_at: string
}

interface ConversationReviewProps {
  tutorId: string
  sessionId: string
  className?: string
}

export function ConversationReview({ tutorId, sessionId, className }: ConversationReviewProps) {
  const t = useTranslations('review')
  const [data, setData] = useState<TranscriptData | null>(null)
  const [loading, setLoading] = useState(true)
  const [flaggingIndex, setFlaggingIndex] = useState<number | null>(null)
  const [flagReason, setFlagReason] = useState('')

  const fetchTranscript = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(
        `${API_BASE}/tutors/${tutorId}/sessions/${sessionId}/transcript`,
        { headers: getAuthHeaders() },
      )
      if (!res.ok) throw new Error(`Failed: ${res.status}`)
      setData(await res.json())
    } catch {
      // Silent fail for MVP -- empty state shown
    } finally {
      setLoading(false)
    }
  }, [tutorId, sessionId])

  useEffect(() => {
    fetchTranscript()
  }, [fetchTranscript])

  const submitFlag = useCallback(
    async (turnIndex: number) => {
      try {
        const res = await fetch(
          `${API_BASE}/tutors/${tutorId}/sessions/${sessionId}/flag`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify({ turn_index: turnIndex, reason: flagReason }),
          },
        )
        if (!res.ok) throw new Error(`Failed: ${res.status}`)
        setFlaggingIndex(null)
        setFlagReason('')
        fetchTranscript()
      } catch {
        // Silent fail for MVP
      }
    },
    [tutorId, sessionId, flagReason, fetchTranscript],
  )

  if (loading) return <SkeletonCard />

  if (!data || data.messages.length === 0) {
    return <EmptyState title={t('empty_title')} description={t('empty_description')} />
  }

  const flaggedIndices = new Set(data.flags.map((f) => f.turn_index))

  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] overflow-hidden',
        className,
      )}
    >
      <div className="px-6 py-4 border-b border-[var(--color-border)]">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('transcript')}</h3>
      </div>

      <div className="max-h-[500px] overflow-y-auto p-4 space-y-3" role="log">
        {data.messages.map((msg, i) => (
          <motion.div
            key={`${msg.role}-${i}`}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            className={cn(
              'flex gap-3',
              msg.role === 'user' ? 'justify-end' : 'justify-start',
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-[var(--radius-md)] p-3 relative group',
                msg.role === 'user'
                  ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                  : 'bg-[var(--color-surface-elevated)] text-[var(--color-text)]',
                flaggedIndices.has(i) && 'ring-2 ring-[var(--color-warning)]',
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p
                className={cn(
                  'text-[10px] mt-1',
                  msg.role === 'user' ? 'text-white/60' : 'text-[var(--color-muted)]',
                )}
              >
                {new Date(msg.created_at).toLocaleTimeString()}
              </p>

              {/* Flag button -- only on assistant messages */}
              {msg.role === 'assistant' && (
                <button
                  type="button"
                  onClick={() => setFlaggingIndex(flaggingIndex === i ? null : i)}
                  title={t('flag_turn')}
                  aria-label={t('flag_turn')}
                  className={cn(
                    'absolute -right-2 -top-2 w-6 h-6 rounded-full',
                    'flex items-center justify-center text-xs',
                    'opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity',
                    flaggedIndices.has(i)
                      ? 'bg-[var(--color-warning)] text-white opacity-100'
                      : 'bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-muted)]',
                  )}
                >
                  {flaggedIndices.has(i) ? '!' : '?'}
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Flag form */}
      <AnimatePresence>
        {flaggingIndex !== null && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-[var(--color-border)] p-4"
          >
            <div className="flex gap-3">
              <input
                type="text"
                value={flagReason}
                onChange={(e) => setFlagReason(e.target.value)}
                placeholder={t('flag_reason')}
                aria-label={t('flag_reason')}
                className={cn(
                  'flex-1 rounded-[var(--radius-md)] border border-[var(--color-border)]',
                  'bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)]',
                )}
              />
              <button
                type="button"
                onClick={() => submitFlag(flaggingIndex)}
                className={cn(
                  'px-4 py-2.5 rounded-[var(--radius-md)]',
                  'bg-[var(--color-warning)] text-white text-sm font-medium',
                )}
              >
                {t('flag_turn')}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
