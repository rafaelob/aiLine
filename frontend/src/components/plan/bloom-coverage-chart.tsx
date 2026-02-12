'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

const BLOOM_LEVELS = [
  'remember',
  'understand',
  'apply',
  'analyze',
  'evaluate',
  'create',
] as const

const BLOOM_COLORS: Record<string, string> = {
  remember: '#DC2626',
  understand: '#E07E34',
  apply: '#D9A006',
  analyze: '#2D8B6E',
  evaluate: '#3B82F6',
  create: '#4338CA',
}

interface CoverageItem {
  standard: string
  name: string
  bloomLevel: string
}

interface BloomCoverageChartProps {
  data: CoverageItem[]
}

/**
 * Horizontal bar chart showing how many standards map to each Bloom level.
 * Uses Recharts BarChart with custom colors per Bloom tier.
 */
export function BloomCoverageChart({ data }: BloomCoverageChartProps) {
  // Count standards per Bloom level
  const counts = BLOOM_LEVELS.map((level) => ({
    level,
    count: data.filter((d) => d.bloomLevel === level).length,
  }))

  // Only show levels that have at least one standard
  const hasData = counts.some((c) => c.count > 0)
  if (!hasData) return null

  return (
    <div
      className="w-full"
      role="img"
      aria-label="Bloom's taxonomy coverage chart"
    >
      <ResponsiveContainer width="100%" height={200}>
        <BarChart
          data={counts}
          layout="vertical"
          margin={{ top: 4, right: 24, bottom: 4, left: 80 }}
        >
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fontSize: 12, fill: 'var(--color-muted)' }}
          />
          <YAxis
            type="category"
            dataKey="level"
            tick={{ fontSize: 12, fill: 'var(--color-text)' }}
            width={76}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-surface-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: '8px',
              fontSize: '12px',
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24}>
            {counts.map((entry) => (
              <Cell
                key={entry.level}
                fill={BLOOM_COLORS[entry.level] ?? '#888'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
