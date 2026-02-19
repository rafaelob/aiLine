'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

interface Standard {
  standard_code: string
  standard_description: string
  student_count: number
  mastered_count: number
  proficient_count: number
  developing_count: number
}

interface ProgressHeatmapProps {
  standards: Standard[]
}

export function ProgressHeatmap({ standards }: ProgressHeatmapProps) {
  const t = useTranslations('progress')

  return (
    <div className={cn(
      'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
      'bg-[var(--color-surface)] p-6 overflow-x-auto'
    )}>
      <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4">
        {t('standards_heatmap')}
      </h2>
      <table className="w-full text-sm" role="grid">
        <thead>
          <tr className="text-left text-xs text-[var(--color-muted)]">
            <th className="pb-3 pr-4 font-medium">{t('standard_column')}</th>
            <th className="pb-3 px-3 font-medium text-center">{t('mastery_levels.mastered')}</th>
            <th className="pb-3 px-3 font-medium text-center">{t('mastery_levels.proficient')}</th>
            <th className="pb-3 px-3 font-medium text-center">{t('mastery_levels.developing')}</th>
            <th className="pb-3 pl-3 font-medium text-center">{t('total_column')}</th>
          </tr>
        </thead>
        <tbody>
          {standards.map((s, i) => {
            const total = s.student_count || 1
            const masteredPct = (s.mastered_count / total) * 100
            return (
              <motion.tr
                key={s.standard_code}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="border-t border-[var(--color-border)]"
              >
                <td className="py-3 pr-4">
                  <div className="font-medium text-[var(--color-text)]">{s.standard_code}</div>
                  {s.standard_description && (
                    <div className="text-xs text-[var(--color-muted)] mt-0.5 truncate max-w-[200px]">
                      {s.standard_description}
                    </div>
                  )}
                </td>
                <td className="py-3 px-3 text-center">
                  <HeatCell value={s.mastered_count} pct={masteredPct} color="var(--color-success)" />
                </td>
                <td className="py-3 px-3 text-center">
                  <HeatCell value={s.proficient_count} pct={(s.proficient_count / total) * 100} color="#3b82f6" />
                </td>
                <td className="py-3 px-3 text-center">
                  <HeatCell value={s.developing_count} pct={(s.developing_count / total) * 100} color="var(--color-warning)" />
                </td>
                <td className="py-3 pl-3 text-center text-[var(--color-muted)]">{s.student_count}</td>
              </motion.tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function HeatCell({ value, pct, color }: { value: number; pct: number; color: string }) {
  const opacity = Math.max(0.15, Math.min(1, pct / 100))
  return (
    <span
      className="inline-flex items-center justify-center w-8 h-8 rounded-[var(--radius-sm)] text-xs font-medium"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} ${Math.round(opacity * 100)}%, transparent)`,
        color: pct > 50 ? 'white' : 'var(--color-text)',
      }}
    >
      {value}
    </span>
  )
}
