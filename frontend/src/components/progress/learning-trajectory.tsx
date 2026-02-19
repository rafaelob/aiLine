'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { cn } from '@/lib/cn'

interface TrajectoryPoint {
  date: string
  score: number
  subject?: string
}

interface LearningTrajectoryProps {
  data: TrajectoryPoint[]
  subjects?: string[]
  className?: string
}

const COLORS = ['var(--color-primary)', '#3b82f6', 'var(--color-success)', 'var(--color-warning)', '#a855f7']

/**
 * Line chart showing score progression over time.
 * Supports multiple subjects as separate series.
 * Full accessibility with role="figure", aria-label summary, and sr-only data table.
 */
export function LearningTrajectory({ data, subjects, className }: LearningTrajectoryProps) {
  const t = useTranslations('progress')

  // Group data by subject for multi-line chart
  const chartData = useMemo(() => {
    if (!subjects || subjects.length === 0) {
      return data.map((d) => ({ date: d.date, score: d.score }))
    }
    // Build date-indexed map
    const dateMap = new Map<string, Record<string, number>>()
    for (const d of data) {
      const key = d.subject ?? 'score'
      if (!dateMap.has(d.date)) dateMap.set(d.date, {})
      dateMap.get(d.date)![key] = d.score
    }
    return Array.from(dateMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, scores]) => ({ date, ...scores }))
  }, [data, subjects])

  const summaryText = useMemo(() => {
    if (data.length === 0) return ''
    const scores = data.map((d) => d.score)
    const avg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
    const min = Math.min(...scores)
    const max = Math.max(...scores)
    return `${data.length} data points, average score ${avg}, range ${min}-${max}`
  }, [data])

  const seriesKeys = subjects && subjects.length > 0 ? subjects : ['score']

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
        {t('student_details')}
      </h2>

      <div
        role="figure"
        aria-label={`Learning trajectory chart. ${summaryText}`}
        tabIndex={0}
        className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)] rounded"
      >
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartData} margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: 'var(--color-muted)' }}
              tickFormatter={(v: string) => {
                const d = new Date(v)
                return `${d.getMonth() + 1}/${d.getDate()}`
              }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: 'var(--color-muted)' }}
              width={36}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
            {seriesKeys.length > 1 && (
              <Legend
                verticalAlign="top"
                wrapperStyle={{ fontSize: '11px', paddingBottom: '8px' }}
              />
            )}
            {seriesKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                name={key}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Screen reader accessible data table */}
      <table className="sr-only">
        <caption>Learning trajectory data</caption>
        <thead>
          <tr>
            <th>Date</th>
            {seriesKeys.map((k) => (
              <th key={k}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chartData.map((row, i) => (
            <tr key={i}>
              <td>{row.date}</td>
              {seriesKeys.map((k) => (
                <td key={k}>{String((row as Record<string, unknown>)[k] ?? '-')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
