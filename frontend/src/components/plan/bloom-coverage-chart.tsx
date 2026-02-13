'use client'

import { useCallback, useRef, useState } from 'react'
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
 *
 * Keyboard accessibility:
 * - Tab into the chart, then use Arrow Up/Down to navigate data points.
 * - Active data point is announced via aria-live region.
 */
export function BloomCoverageChart({ data }: BloomCoverageChartProps) {
  const [activeIndex, setActiveIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)

  // Count standards per Bloom level
  const counts = BLOOM_LEVELS.map((level) => ({
    level,
    count: data.filter((d) => d.bloomLevel === level).length,
  }))

  // Only show levels that have at least one standard
  const hasData = counts.some((c) => c.count > 0)

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const nonZeroCounts = counts.filter((c) => c.count > 0)
      if (nonZeroCounts.length === 0) return

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault()
        setActiveIndex((prev) => {
          const next = prev + 1
          return next >= counts.length ? 0 : next
        })
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault()
        setActiveIndex((prev) => {
          const next = prev - 1
          return next < 0 ? counts.length - 1 : next
        })
      } else if (e.key === 'Escape') {
        setActiveIndex(-1)
        containerRef.current?.blur()
      }
    },
    [counts],
  )

  if (!hasData) return null

  const activeItem = activeIndex >= 0 ? counts[activeIndex] : null
  const announcement = activeItem
    ? `${activeItem.level}: ${activeItem.count} standard${activeItem.count !== 1 ? 's' : ''}`
    : ''

  // Build an accessible summary of all data points
  const dataSummary = counts
    .filter((c) => c.count > 0)
    .map((c) => `${c.level}: ${c.count}`)
    .join(', ')

  return (
    <div className="w-full">
      <div
        ref={containerRef}
        role="figure"
        aria-label={`Bloom's taxonomy coverage chart. ${dataSummary}`}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (activeIndex < 0) setActiveIndex(0)
        }}
        onBlur={() => setActiveIndex(-1)}
        className="focus-visible:outline-2 focus-visible:outline-offset-2
                   focus-visible:outline-[var(--color-primary)] rounded"
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
              {counts.map((entry, i) => (
                <Cell
                  key={entry.level}
                  fill={BLOOM_COLORS[entry.level] ?? '#888'}
                  opacity={activeIndex >= 0 && activeIndex !== i ? 0.4 : 1}
                  stroke={activeIndex === i ? '#000' : 'none'}
                  strokeWidth={activeIndex === i ? 2 : 0}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Screen reader live region for keyboard navigation */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>
    </div>
  )
}
