'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface RecordProgressFormProps {
  onSuccess: () => void
  className?: string
}

export function RecordProgressForm({ onSuccess, className }: RecordProgressFormProps) {
  const t = useTranslations('progress')
  const [studentId, setStudentId] = useState('')
  const [studentName, setStudentName] = useState('')
  const [standardCode, setStandardCode] = useState('')
  const [standardDesc, setStandardDesc] = useState('')
  const [mastery, setMastery] = useState('developing')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/progress/record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          student_id: studentId,
          student_name: studentName,
          standard_code: standardCode,
          standard_description: standardDesc,
          mastery_level: mastery,
        }),
      })
      if (!res.ok) throw new Error(`Failed: ${res.status}`)
      onSuccess()
    } catch {
      // Silent fail for MVP
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-6 space-y-4',
        className
      )}
    >
      <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('record_progress')}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="rp-student-id" className="block text-xs font-medium text-[var(--color-muted)] mb-1">
            {t('student_id_label')}
          </label>
          <input
            id="rp-student-id"
            type="text"
            placeholder="Student ID"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            required
            aria-required="true"
            className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]"
          />
        </div>
        <div>
          <label htmlFor="rp-student-name" className="block text-xs font-medium text-[var(--color-muted)] mb-1">
            {t('student_name_label')}
          </label>
          <input
            id="rp-student-name"
            type="text"
            placeholder="Student Name"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]"
          />
        </div>
        <div>
          <label htmlFor="rp-standard-code" className="block text-xs font-medium text-[var(--color-muted)] mb-1">
            {t('standard_code_label')}
          </label>
          <input
            id="rp-standard-code"
            type="text"
            placeholder="Standard Code (e.g. EF06MA01)"
            value={standardCode}
            onChange={(e) => setStandardCode(e.target.value)}
            required
            aria-required="true"
            className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]"
          />
        </div>
        <div>
          <label htmlFor="rp-standard-desc" className="block text-xs font-medium text-[var(--color-muted)] mb-1">
            {t('standard_desc_label')}
          </label>
          <input
            id="rp-standard-desc"
            type="text"
            placeholder="Standard Description"
            value={standardDesc}
            onChange={(e) => setStandardDesc(e.target.value)}
            className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]"
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div>
          <label htmlFor="rp-mastery" className="sr-only">
            {t('mastery_level_label')}
          </label>
          <select
            id="rp-mastery"
            value={mastery}
            onChange={(e) => setMastery(e.target.value)}
            className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-bg)] p-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]"
          >
          <option value="not_started">{t('mastery_levels.not_started')}</option>
          <option value="developing">{t('mastery_levels.developing')}</option>
          <option value="proficient">{t('mastery_levels.proficient')}</option>
          <option value="mastered">{t('mastery_levels.mastered')}</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className={cn(
            'px-5 py-2.5 rounded-[var(--radius-md)]',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'text-sm font-medium hover:bg-[var(--color-primary-hover)]',
            'disabled:opacity-50'
          )}
        >
          {submitting ? '...' : t('record_progress')}
        </button>
      </div>
    </form>
  )
}
