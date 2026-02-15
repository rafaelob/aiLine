'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, type Variants } from 'motion/react'
import { cn } from '@/lib/cn'
import { EmptyState } from '@/components/shared/empty-state'
import { SkeletonCard } from '@/components/shared/skeleton'
import { ProgressHeatmap } from './progress-heatmap'
import { StudentProgressCard } from './student-progress-card'
import { RecordProgressForm } from './record-progress-form'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface DashboardData {
  teacher_id: string
  total_students: number
  total_standards: number
  mastery_distribution: Record<string, number>
  students: Array<{
    student_id: string
    student_name: string
    standards_count: number
    mastered_count: number
    proficient_count: number
    developing_count: number
    last_activity: string | null
  }>
  standards: Array<{
    standard_code: string
    standard_description: string
    student_count: number
    mastered_count: number
    proficient_count: number
    developing_count: number
  }>
}

export function ProgressDashboard() {
  const t = useTranslations('progress')
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/progress/dashboard`, {
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

  useEffect(() => { fetchDashboard() }, [fetchDashboard])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <SkeletonCard />
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="rounded-[var(--radius-md)] p-4 text-center bg-[var(--color-error)]/10 text-[var(--color-error)]">
        <p className="text-sm">{error}</p>
        <button type="button" onClick={fetchDashboard} className="mt-2 text-sm underline">
          Retry
        </button>
      </div>
    )
  }

  if (!data || data.total_students === 0) {
    return (
      <div className="space-y-6">
        <EmptyState
          icon={<EmptyProgressIcon />}
          title={t('empty_title')}
          description={t('empty_description')}
          action={
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className={cn(
                'px-5 py-2.5 rounded-[var(--radius-md)]',
                'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                'text-sm font-medium hover:bg-[var(--color-primary-hover)]'
              )}
            >
              {t('record_progress')}
            </button>
          }
        />
        {showForm && <RecordProgressForm onSuccess={() => { setShowForm(false); fetchDashboard() }} />}
      </div>
    )
  }

  const mastery = data.mastery_distribution
  const total = Object.values(mastery).reduce((a, b) => a + b, 0) || 1

  return (
    <div className="space-y-8">
      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label={t('total_students')} value={data.total_students} color="var(--color-primary)" icon={<PeopleIcon />} />
        <StatCard label={t('total_standards')} value={data.total_standards} color="var(--color-secondary, var(--color-primary))" icon={<DocumentIcon />} />
        <StatCard label={t('mastery_levels.mastered')} value={mastery.mastered ?? 0} color="var(--color-success)" icon={<CheckCircleIcon />} />
        <StatCard label={t('mastery_levels.developing')} value={mastery.developing ?? 0} color="var(--color-warning)" icon={<TrendingUpIcon />} />
      </div>

      {/* Mastery distribution bar */}
      <div className="rounded-2xl glass p-6">
        <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4">
          {t('standards_heatmap')}
        </h2>
        <div className="flex h-6 rounded-full overflow-hidden bg-[var(--color-surface-elevated)]">
          {mastery.mastered > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(mastery.mastered / total) * 100}%` }}
              className="bg-[var(--color-success)]"
              title={`${t('mastery_levels.mastered')}: ${mastery.mastered}`}
            />
          )}
          {mastery.proficient > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(mastery.proficient / total) * 100}%` }}
              className="bg-blue-500"
              title={`${t('mastery_levels.proficient')}: ${mastery.proficient}`}
            />
          )}
          {mastery.developing > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(mastery.developing / total) * 100}%` }}
              className="bg-[var(--color-warning)]"
              title={`${t('mastery_levels.developing')}: ${mastery.developing}`}
            />
          )}
        </div>
        <div className="flex gap-4 mt-3 text-xs text-[var(--color-muted)]">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[var(--color-success)]" />{t('mastery_levels.mastered')}</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500" />{t('mastery_levels.proficient')}</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[var(--color-warning)]" />{t('mastery_levels.developing')}</span>
        </div>
      </div>

      {/* Standards heatmap */}
      {data.standards.length > 0 && <ProgressHeatmap standards={data.standards} />}

      {/* Student cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[var(--color-text)]">
            {t('student_details')}
          </h2>
          <button
            type="button"
            onClick={() => setShowForm(!showForm)}
            className={cn(
              'px-5 py-2.5 rounded-xl btn-shimmer',
              'text-xs font-semibold text-[var(--color-on-primary)]',
              'shadow-[var(--shadow-md)]',
              'hover:shadow-[var(--shadow-lg)] hover:scale-[1.02]',
              'active:scale-95',
              'transition-all duration-300'
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            {t('record_progress')}
          </button>
        </div>
        {showForm && <RecordProgressForm onSuccess={() => { setShowForm(false); fetchDashboard() }} className="mb-6" />}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
          }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {data.students.map((s) => (
            <motion.div
              key={s.student_id}
              variants={{
                hidden: { opacity: 0, y: 12 },
                visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200, damping: 24 } },
              }}
            >
              <StudentProgressCard student={s} />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color, icon }: { label: string; value: number; color: string; icon: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="gradient-border-glass rounded-2xl glass p-5 flex items-center gap-4 card-hover group relative overflow-hidden"
    >
      <div
        className="flex items-center justify-center w-12 h-12 icon-orb shrink-0"
        style={{ background: `linear-gradient(135deg, ${color}, var(--color-secondary))` }}
        aria-hidden="true"
      >
        <span className="text-white">{icon}</span>
      </div>
      <div>
        <p className="text-2xl font-bold text-[var(--color-text)]">{value}</p>
        <p className="text-xs text-[var(--color-muted)]">{label}</p>
      </div>
    </motion.div>
  )
}

function EmptyProgressIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="36" y1="40" x2="36" y2="20" />
      <line x1="24" y1="40" x2="24" y2="8" />
      <line x1="12" y1="40" x2="12" y2="28" />
    </svg>
  )
}

function PeopleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
    </svg>
  )
}

function DocumentIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
    </svg>
  )
}

function CheckCircleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  )
}

function TrendingUpIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
    </svg>
  )
}
