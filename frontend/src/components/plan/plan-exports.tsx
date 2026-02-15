'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { API_BASE } from '@/lib/api'

const EXPORT_VARIANTS = [
  'teacher_plan',
  'student_plan',
  'visual_schedule',
  'simplified',
  'high_contrast',
  'audio_script',
  'sign_language',
  'parent_guide',
  'assessment',
  'curriculum_map',
] as const

type ExportVariant = (typeof EXPORT_VARIANTS)[number]

interface PlanExportsProps {
  planId: string
}

/**
 * Export variant selector and preview.
 * Allows selection of one of the 10 export variants.
 */
export function PlanExports({ planId }: PlanExportsProps) {
  const t = useTranslations('exports')
  const tpe = useTranslations('plan_exports')
  const [selected, setSelected] = useState<ExportVariant | null>(null)
  const [loading, setLoading] = useState(false)
  const [content, setContent] = useState<string | null>(null)

  async function handleSelect(variant: ExportVariant) {
    setSelected(variant)
    setLoading(true)
    setContent(null)

    try {
      const res = await fetch(
        `${API_BASE}/plans/${planId}/exports/${variant}`
      )
      if (!res.ok) throw new Error(`Export fetch failed: ${res.status}`)
      const data = await res.json()
      setContent(data.content ?? JSON.stringify(data, null, 2))
    } catch {
      setContent(tpe('unavailable'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Title with icon-orb */}
      <motion.div className="flex items-center gap-3" variants={itemVariants}>
        <div
          className="flex items-center justify-center w-8 h-8 icon-orb shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
          aria-hidden="true"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-[var(--color-text)]">
          {t('title')}
        </h3>
      </motion.div>

      {/* Variant grid */}
      <motion.div className="glass rounded-2xl p-4" variants={itemVariants}>
        <div
          className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3"
          role="listbox"
          aria-label={t('select')}
        >
          {EXPORT_VARIANTS.map((variant) => (
            <button
              key={variant}
              type="button"
              role="option"
              aria-selected={selected === variant}
              onClick={() => handleSelect(variant)}
              className={cn(
                'flex flex-col items-center gap-2 p-4',
                'rounded-xl glass card-hover text-center',
                'transition-all text-sm',
                selected === variant
                  ? 'gradient-border-glass text-[var(--color-primary)]'
                  : 'text-[var(--color-text)]'
              )}
            >
              <div
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-lg',
                  selected === variant
                    ? 'icon-orb'
                    : 'text-[var(--color-muted)]'
                )}
                style={
                  selected === variant
                    ? { background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }
                    : undefined
                }
              >
                <ExportIcon variant={variant} selected={selected === variant} />
              </div>
              <span className="text-xs font-medium">
                {t(`variants.${variant}`)}
              </span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Preview area */}
      {selected && (
        <motion.div
          className="glass rounded-2xl gradient-border-glass p-6"
          variants={itemVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-[var(--color-text)]">
              {t(`variants.${selected}`)}
            </h4>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3" role="status">
              <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-[var(--color-muted)]">
                {tpe('loading')}
              </span>
            </div>
          ) : (
            <pre
              className={cn(
                'whitespace-pre-wrap text-sm text-[var(--color-text)]',
                'max-h-96 overflow-y-auto p-4',
                'glass rounded-xl'
              )}
            >
              {content}
            </pre>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}

function ExportIcon({ variant, selected }: { variant: ExportVariant; selected: boolean }) {
  const iconMap: Record<string, string> = {
    teacher_plan: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
    student_plan: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2',
    visual_schedule: 'M3 3h18v18H3zM3 9h18M9 3v18',
    simplified: 'M4 6h16M4 12h10M4 18h6',
    high_contrast: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z',
    audio_script: 'M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z',
    sign_language: 'M18 11V6a2 2 0 0 0-4 0M14 10V4a2 2 0 0 0-4 0M10 10V5a2 2 0 0 0-4 0v9',
    parent_guide: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z',
    assessment: 'M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11',
    curriculum_map: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z',
  }

  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke={selected ? 'white' : 'currentColor'}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={iconMap[variant] ?? iconMap.teacher_plan} />
    </svg>
  )
}
