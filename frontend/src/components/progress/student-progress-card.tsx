'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

interface StudentData {
  student_id: string
  student_name: string
  standards_count: number
  mastered_count: number
  proficient_count: number
  developing_count: number
  last_activity: string | null
}

interface StudentProgressCardProps {
  student: StudentData
}

export function StudentProgressCard({ student }: StudentProgressCardProps) {
  const t = useTranslations('progress')
  const total = student.standards_count || 1
  const masteredPct = Math.round((student.mastered_count / total) * 100)
  const proficientPct = Math.round((student.proficient_count / total) * 100)
  const developingPct = Math.round((student.developing_count / total) * 100)

  return (
    <div className="glass card-hover rounded-2xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-base font-semibold text-[var(--color-text)] truncate">
            {student.student_name || student.student_id}
          </p>
          <p className="text-xs text-[var(--color-muted)] mt-0.5">
            {student.standards_count} {t('total_standards').toLowerCase()}
          </p>
        </div>
        <div
          className={cn(
            'flex items-center justify-center w-12 h-12 rounded-full shrink-0',
            'text-sm font-bold shadow-sm',
            masteredPct >= 80 ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' :
            masteredPct >= 50 ? 'bg-blue-500/15 text-blue-600' :
            'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
          )}
        >
          {masteredPct}%
        </div>
      </div>

      {/* Progress bars with labels */}
      <div className="space-y-2.5">
        {student.mastered_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 min-w-[80px]">
              <MasteredIcon />
              <span className="text-[10px] text-[var(--color-muted)]">{t('mastery_levels.mastered')}</span>
            </div>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-[var(--color-surface-elevated)]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${masteredPct}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, var(--color-success), #10b981)' }}
              />
            </div>
            <span className="text-[10px] font-medium text-[var(--color-text)] min-w-[28px] text-right">{masteredPct}%</span>
          </div>
        )}
        {student.proficient_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 min-w-[80px]">
              <ProficientIcon />
              <span className="text-[10px] text-[var(--color-muted)]">{t('mastery_levels.proficient')}</span>
            </div>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-[var(--color-surface-elevated)]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${proficientPct}%` }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, #3b82f6, #60a5fa)' }}
              />
            </div>
            <span className="text-[10px] font-medium text-[var(--color-text)] min-w-[28px] text-right">{proficientPct}%</span>
          </div>
        )}
        {student.developing_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 min-w-[80px]">
              <DevelopingIcon />
              <span className="text-[10px] text-[var(--color-muted)]">{t('mastery_levels.developing')}</span>
            </div>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-[var(--color-surface-elevated)]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${developingPct}%` }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, var(--color-warning), #fbbf24)' }}
              />
            </div>
            <span className="text-[10px] font-medium text-[var(--color-text)] min-w-[28px] text-right">{developingPct}%</span>
          </div>
        )}
      </div>

      {student.last_activity && (
        <div className="pt-2 border-t border-[var(--color-border)]">
          <p className="text-[10px] text-[var(--color-muted)] flex items-center gap-1">
            <ClockIcon />
            {t('last_activity')}: {new Date(student.last_activity).toLocaleDateString()}
          </p>
        </div>
      )}
    </div>
  )
}

function MasteredIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="5" fill="var(--color-success)" opacity="0.2" />
      <path d="M4 6L5.5 7.5L8.5 4.5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ProficientIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="5" fill="#3b82f6" opacity="0.2" />
      <circle cx="6" cy="6" r="2.5" fill="#3b82f6" />
    </svg>
  )
}

function DevelopingIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="5" fill="var(--color-warning)" opacity="0.2" />
      <path d="M6 4V6L7.5 7.5" stroke="var(--color-warning)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ClockIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <path d="M5 2.5V5L6.5 6.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" opacity="0.5" />
    </svg>
  )
}
