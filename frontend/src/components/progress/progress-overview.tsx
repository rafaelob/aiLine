'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { cn } from '@/lib/cn'

interface MasteryData {
  topic: string
  mastered: number
  proficient: number
  developing: number
  not_started: number
}

interface ProgressOverviewProps {
  data: MasteryData[]
  className?: string
}

/**
 * Bar chart showing mastery levels across topics/skills.
 * Uses Recharts with stacked bars and full accessibility:
 * - role="figure" with descriptive aria-label
 * - sr-only data table for screen readers
 */
export function ProgressOverview({ data, className }: ProgressOverviewProps) {
  const t = useTranslations('progress')

  const chartSummary = useMemo(() => {
    const totals = { mastered: 0, proficient: 0, developing: 0, not_started: 0 }
    for (const d of data) {
      totals.mastered += d.mastered
      totals.proficient += d.proficient
      totals.developing += d.developing
      totals.not_started += d.not_started
    }
    return `${data.length} topics: ${totals.mastered} mastered, ${totals.proficient} proficient, ${totals.developing} developing, ${totals.not_started} not started`
  }, [data])

  if (data.length === 0) return null

  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-6',
        className,
      )}
    >
      <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4">
        {t('dashboard_title')}
      </h2>

      <div
        role="figure"
        aria-label={`${t('dashboard_title')}. ${chartSummary}`}
        tabIndex={0}
        className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)] rounded"
      >
        <ResponsiveContainer width="100%" height={Math.max(200, data.length * 40)}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 24, bottom: 4, left: 100 }}
          >
            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fontSize: 12, fill: 'var(--color-muted)' }}
            />
            <YAxis
              type="category"
              dataKey="topic"
              tick={{ fontSize: 11, fill: 'var(--color-text)' }}
              width={96}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
            <Legend
              verticalAlign="top"
              wrapperStyle={{ fontSize: '11px', paddingBottom: '8px' }}
            />
            <Bar
              dataKey="mastered"
              stackId="mastery"
              name={t('mastery_levels.mastered')}
              fill="var(--color-success)"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="proficient"
              stackId="mastery"
              name={t('mastery_levels.proficient')}
              fill="#3b82f6"
            />
            <Bar
              dataKey="developing"
              stackId="mastery"
              name={t('mastery_levels.developing')}
              fill="var(--color-warning)"
            />
            <Bar
              dataKey="not_started"
              stackId="mastery"
              name={t('mastery_levels.not_started')}
              fill="var(--color-muted)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Screen reader accessible data table */}
      <table className="sr-only">
        <caption>{t('dashboard_title')}</caption>
        <thead>
          <tr>
            <th>{t('standard_column')}</th>
            <th>{t('mastery_levels.mastered')}</th>
            <th>{t('mastery_levels.proficient')}</th>
            <th>{t('mastery_levels.developing')}</th>
            <th>{t('mastery_levels.not_started')}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.topic}>
              <td>{d.topic}</td>
              <td>{d.mastered}</td>
              <td>{d.proficient}</td>
              <td>{d.developing}</td>
              <td>{d.not_started}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
