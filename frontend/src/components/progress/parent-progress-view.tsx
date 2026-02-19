'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { EmptyState } from '@/components/shared/empty-state'
import { SkeletonCard } from '@/components/shared/skeleton'
import { StudentProgressCard } from './student-progress-card'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface ChildProgress {
  student_id: string
  student_name: string
  standards_count: number
  mastered_count: number
  proficient_count: number
  developing_count: number
  last_activity: string | null
}

interface ParentDashboardData {
  parent_id: string
  children: ChildProgress[]
}

/**
 * Simplified progress view for parents showing linked children's progress.
 * Role-aware: shows only children linked to the authenticated parent.
 * Falls back to empty state when no children are linked.
 */
export function ParentProgressView() {
  const t = useTranslations('progress')
  const [data, setData] = useState<ParentDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProgress = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/progress/parent`, {
        headers: { ...getAuthHeaders() },
      })
      if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`)
      const json = await res.json()
      setData(json)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load progress')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchProgress() }, [fetchProgress])

  if (loading) {
    return (
      <div className="space-y-6" aria-busy="true">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="rounded-[var(--radius-md)] p-4 text-center bg-[var(--color-error)]/10 text-[var(--color-error)]">
        <p className="text-sm">{error}</p>
        <button type="button" onClick={fetchProgress} className="mt-2 text-sm underline">
          {t('retry')}
        </button>
      </div>
    )
  }

  if (!data || data.children.length === 0) {
    return (
      <EmptyState
        icon={<EmptyChildrenIcon />}
        title={t('parent_empty_title')}
        description={t('parent_empty_description')}
      />
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-[var(--color-muted)]">
        {t('parent_subtitle', { count: data.children.length })}
      </p>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
        }}
        className={cn(
          'grid gap-4',
          data.children.length === 1
            ? 'grid-cols-1 max-w-md'
            : 'grid-cols-1 sm:grid-cols-2',
        )}
      >
        {data.children.map((child) => (
          <motion.div
            key={child.student_id}
            variants={{
              hidden: { opacity: 0, y: 12 },
              visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200, damping: 24 } },
            }}
          >
            <StudentProgressCard student={child} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}

function EmptyChildrenIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="24" cy="16" r="8" />
      <path d="M8 40c0-8.837 7.163-16 16-16s16 7.163 16 16" />
    </svg>
  )
}
