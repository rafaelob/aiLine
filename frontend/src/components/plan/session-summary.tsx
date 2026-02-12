'use client'

import { useCallback, useState } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { StudyPlan } from '@/types/plan'
import { BloomCoverageChart } from './bloom-coverage-chart'

interface SessionSummaryProps {
  plan: StudyPlan
}

const BLOOM_LEVELS = [
  'remember',
  'understand',
  'apply',
  'analyze',
  'evaluate',
  'create',
] as const

/**
 * Teacher Impact View / Session Summary.
 * Shows standards coverage, accessibility adaptations, and recommended next steps.
 * Includes "Copy as Markdown" export.
 */
export function SessionSummary({ plan }: SessionSummaryProps) {
  const t = useTranslations('session')
  const [copied, setCopied] = useState(false)

  // Derive coverage data from plan's curriculum alignment
  const coverageData = plan.curriculum_alignment.map((alignment) => ({
    standard: alignment.standard_id,
    name: alignment.standard_name,
    description: alignment.description,
    bloomLevel: inferBloomLevel(alignment.description),
  }))

  // Collect all adaptations across activities
  const allAdaptations = plan.activities.flatMap((activity) =>
    activity.adaptations.map((a) => ({
      activity: activity.title,
      profile: a.profile,
      description: a.description,
    }))
  )

  const handleCopyMarkdown = useCallback(async () => {
    const md = generateMarkdown(plan, coverageData, allAdaptations, t)
    try {
      await navigator.clipboard.writeText(md)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: no-op
    }
  }, [plan, coverageData, allAdaptations, t])

  const handleDownloadJSON = useCallback(() => {
    const data = {
      plan_id: plan.id,
      title: plan.title,
      subject: plan.subject,
      grade: plan.grade,
      standards_coverage: coverageData,
      adaptations: allAdaptations,
      objectives: plan.objectives,
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `session-note-${plan.id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [plan, coverageData, allAdaptations])

  return (
    <div className="space-y-8">
      {/* Export buttons */}
      <div className="flex items-center gap-3 justify-end">
        <button
          type="button"
          onClick={handleCopyMarkdown}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium',
            'rounded-[var(--radius-md)] border border-[var(--color-border)]',
            'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]',
            'transition-colors'
          )}
          aria-label={t('copy_markdown')}
        >
          <CopyIcon />
          {copied ? t('copied') : t('copy_markdown')}
        </button>
        <button
          type="button"
          onClick={handleDownloadJSON}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium',
            'rounded-[var(--radius-md)] border border-[var(--color-border)]',
            'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]',
            'transition-colors'
          )}
          aria-label={t('download_json')}
        >
          <DownloadIcon />
          {t('download_json')}
        </button>
      </div>

      {/* 1. Standards Coverage */}
      <section aria-labelledby="standards-heading">
        <h3
          id="standards-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-4"
        >
          {t('standards_coverage')}
        </h3>

        {coverageData.length > 0 ? (
          <div className="space-y-4">
            <BloomCoverageChart data={coverageData} />

            {/* Standards table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="text-left py-2 px-3 text-[var(--color-muted)] font-medium">
                      {t('standard_code')}
                    </th>
                    <th className="text-left py-2 px-3 text-[var(--color-muted)] font-medium">
                      {t('standard_name')}
                    </th>
                    <th className="text-left py-2 px-3 text-[var(--color-muted)] font-medium">
                      {t('bloom_level')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {coverageData.map((item, i) => (
                    <tr
                      key={i}
                      className="border-b border-[var(--color-border)] last:border-0"
                    >
                      <td className="py-2 px-3 text-[var(--color-text)] font-mono text-xs">
                        {item.standard}
                      </td>
                      <td className="py-2 px-3 text-[var(--color-text)]">
                        {item.name}
                      </td>
                      <td className="py-2 px-3">
                        <BloomBadge level={item.bloomLevel} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="text-sm text-[var(--color-muted)]">
            {t('no_standards')}
          </p>
        )}
      </section>

      {/* 2. Accessibility Adaptations */}
      <section aria-labelledby="adaptations-heading">
        <h3
          id="adaptations-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-4"
        >
          {t('adaptations_applied')}
        </h3>

        {allAdaptations.length > 0 ? (
          <ul className="space-y-3">
            {allAdaptations.map((adapt, i) => (
              <li
                key={i}
                className={cn(
                  'flex items-start gap-3 p-3 rounded-[var(--radius-md)]',
                  'bg-[var(--color-secondary)]/5 border-l-3 border-[var(--color-secondary)]'
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-[var(--color-secondary)] uppercase">
                      {adapt.profile}
                    </span>
                    <span className="text-xs text-[var(--color-muted)]">
                      {adapt.activity}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--color-text)]">
                    {adapt.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--color-muted)]">
            {t('no_adaptations')}
          </p>
        )}
      </section>

      {/* 3. Recommended Next Steps */}
      <section aria-labelledby="next-steps-heading">
        <h3
          id="next-steps-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-4"
        >
          {t('next_steps')}
        </h3>
        <div className="space-y-3">
          <NextStepCard
            icon={<AssessmentIcon />}
            title={t('micro_assessment')}
            description={t('micro_assessment_desc', {
              topic: plan.objectives[0] ?? plan.subject,
            })}
          />
          <NextStepCard
            icon={<PracticeIcon />}
            title={t('practice_activity')}
            description={t('practice_activity_desc', {
              subject: plan.subject,
            })}
          />
          <NextStepCard
            icon={<NextTopicIcon />}
            title={t('next_topic')}
            description={t('next_topic_desc', {
              grade: plan.grade,
              subject: plan.subject,
            })}
          />
        </div>
      </section>
    </div>
  )
}

/* ===== Helpers ===== */

function inferBloomLevel(description: string): (typeof BLOOM_LEVELS)[number] {
  const lower = description.toLowerCase()
  if (/creat|design|produc|compor|inventar/.test(lower)) return 'create'
  if (/evaluat|judg|justif|avaliar|julgar/.test(lower)) return 'evaluate'
  if (/analy[sz]|compar|examin|analisar/.test(lower)) return 'analyze'
  if (/appl|solv|demonstrat|aplicar|resolver/.test(lower)) return 'apply'
  if (/explain|describ|summariz|explicar|descrever/.test(lower)) return 'understand'
  return 'remember'
}

const BLOOM_COLORS: Record<string, string> = {
  remember: 'var(--color-error)',
  understand: '#E07E34',
  apply: '#D9A006',
  analyze: '#2D8B6E',
  evaluate: 'var(--color-primary)',
  create: '#4338CA',
}

function BloomBadge({ level }: { level: string }) {
  const color = BLOOM_COLORS[level] ?? 'var(--color-muted)'
  return (
    <span
      className="text-xs font-medium px-2 py-0.5 rounded-full"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
        color,
      }}
    >
      {level}
    </span>
  )
}

function NextStepCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-[var(--radius-md)]',
        'bg-[var(--color-surface-elevated)] border border-[var(--color-border)]'
      )}
    >
      <div className="text-[var(--color-primary)] shrink-0 mt-0.5">
        {icon}
      </div>
      <div>
        <h4 className="text-sm font-medium text-[var(--color-text)]">
          {title}
        </h4>
        <p className="text-xs text-[var(--color-muted)] mt-1">
          {description}
        </p>
      </div>
    </div>
  )
}

function generateMarkdown(
  plan: StudyPlan,
  coverage: Array<{
    standard: string
    name: string
    bloomLevel: string
  }>,
  adaptations: Array<{
    activity: string
    profile: string
    description: string
  }>,
  t: (key: string) => string
): string {
  const lines: string[] = []
  lines.push(`# ${t('session_note')}: ${plan.title}`)
  lines.push(`**${plan.subject}** | ${plan.grade}`)
  lines.push('')

  lines.push(`## ${t('standards_coverage')}`)
  if (coverage.length > 0) {
    lines.push('| Code | Name | Bloom |')
    lines.push('|------|------|-------|')
    for (const c of coverage) {
      lines.push(`| ${c.standard} | ${c.name} | ${c.bloomLevel} |`)
    }
  } else {
    lines.push(t('no_standards'))
  }
  lines.push('')

  lines.push(`## ${t('adaptations_applied')}`)
  if (adaptations.length > 0) {
    for (const a of adaptations) {
      lines.push(`- **[${a.profile}]** ${a.activity}: ${a.description}`)
    }
  } else {
    lines.push(t('no_adaptations'))
  }
  lines.push('')

  lines.push(`## ${t('next_steps')}`)
  lines.push(`- ${t('micro_assessment')}`)
  lines.push(`- ${t('practice_activity')}`)
  lines.push(`- ${t('next_topic')}`)

  return lines.join('\n')
}

/* ===== Icons ===== */

function CopyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  )
}

function DownloadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

function AssessmentIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
  )
}

function PracticeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function NextTopicIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  )
}
