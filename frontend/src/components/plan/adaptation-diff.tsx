'use client'

import { useState, useMemo, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { StudyPlan, Activity, Adaptation } from '@/types/plan'

/** Accessibility profile identifiers for diff comparison. */
type DiffProfile = 'standard' | 'tea' | 'tdah' | 'dyslexia' | 'hearing'

interface AdaptationDiffProps {
  plan: StudyPlan
  className?: string
}

const PROFILES: { id: DiffProfile; labelKey: string; color: string }[] = [
  { id: 'standard', labelKey: 'standard', color: 'var(--color-muted)' },
  { id: 'tea', labelKey: 'asd', color: '#2D8B6E' },
  { id: 'tdah', labelKey: 'adhd', color: '#E07E34' },
  { id: 'dyslexia', labelKey: 'dyslexia', color: '#3B7DD8' },
  { id: 'hearing', labelKey: 'hearing', color: '#4338CA' },
]

/**
 * Split-pane diff view comparing a standard curriculum plan
 * against AI-adapted versions for different accessibility profiles.
 * Highlights additions (green), modifications (yellow), and removals (strikethrough).
 */
export function AdaptationDiff({ plan, className }: AdaptationDiffProps) {
  const t = useTranslations('adaptation')
  const [activeProfile, setActiveProfile] = useState<DiffProfile>('tea')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const handleProfileChange = useCallback((profile: DiffProfile) => {
    setActiveProfile(profile)
  }, [])

  const standardContent = useMemo(() => buildStandardContent(plan), [plan])
  const adaptedContent = useMemo(
    () => buildAdaptedContent(plan, activeProfile),
    [plan, activeProfile],
  )
  const diffBlocks = useMemo(
    () => computeDiffBlocks(standardContent, adaptedContent),
    [standardContent, adaptedContent],
  )

  const activeProfileMeta = PROFILES.find((p) => p.id === activeProfile)

  return (
    <section
      className={cn('space-y-4', className)}
      aria-label={t('section_label')}
    >
      {/* Profile selector tabs */}
      <div
        role="tablist"
        aria-label={t('profile_tabs_label')}
        className="glass rounded-xl p-1 inline-flex gap-1 flex-wrap"
      >
        {PROFILES.filter((p) => p.id !== 'standard').map((profile) => (
          <button
            key={profile.id}
            type="button"
            role="tab"
            aria-selected={activeProfile === profile.id}
            aria-controls="diff-adapted-panel"
            onClick={() => handleProfileChange(profile.id)}
            className={cn(
              'relative px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              activeProfile === profile.id
                ? 'text-[var(--color-on-primary)]'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50',
            )}
          >
            {activeProfile === profile.id && (
              <motion.span
                layoutId="diff-profile-indicator"
                className="absolute inset-0 rounded-lg"
                style={{ backgroundColor: profile.color, zIndex: -1 }}
                transition={
                  noMotion
                    ? { duration: 0 }
                    : { type: 'spring', stiffness: 500, damping: 30 }
                }
              />
            )}
            {t(`profiles.${profile.labelKey}`)}
          </button>
        ))}
      </div>

      {/* Diff legend */}
      <div className="flex flex-wrap gap-4 text-xs text-[var(--color-muted)]" aria-label={t('legend_label')}>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-[var(--color-success)]/20 border border-[var(--color-success)]/40" aria-hidden="true" />
          {t('legend_addition')}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-[var(--color-warning)]/20 border border-[var(--color-warning)]/40" aria-hidden="true" />
          {t('legend_modification')}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-[var(--color-error)]/10 border border-[var(--color-error)]/30" aria-hidden="true" />
          {t('legend_removal')}
        </span>
      </div>

      {/* Split pane: Standard vs Adapted */}
      <div
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
        role="region"
        aria-label={t('comparison_label')}
      >
        {/* Standard panel */}
        <DiffPanel
          title={t('standard_title')}
          panelId="diff-standard-panel"
          contentLabel={t('standard_content_label')}
          noMotion={noMotion}
        >
          {standardContent.map((block, i) => (
            <DiffBlock key={i} block={block} side="standard" />
          ))}
        </DiffPanel>

        {/* Adapted panel */}
        <DiffPanel
          title={t('adapted_title', { profile: activeProfileMeta ? t(`profiles.${activeProfileMeta.labelKey}`) : '' })}
          panelId="diff-adapted-panel"
          contentLabel={t('adapted_content_label')}
          noMotion={noMotion}
          accentColor={activeProfileMeta?.color}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={activeProfile}
              initial={noMotion ? undefined : { opacity: 0, x: 12 }}
              animate={noMotion ? undefined : { opacity: 1, x: 0 }}
              exit={noMotion ? undefined : { opacity: 0, x: -12 }}
              transition={noMotion ? undefined : { duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            >
              {diffBlocks.map((block, i) => (
                <DiffBlock key={i} block={block} side="adapted" />
              ))}
            </motion.div>
          </AnimatePresence>
        </DiffPanel>
      </div>

      {/* Adaptation summary */}
      <div className="glass rounded-xl p-4">
        <p className="text-sm text-[var(--color-muted)]">
          {t('summary', {
            additions: diffBlocks.filter((b) => b.type === 'addition').length,
            modifications: diffBlocks.filter((b) => b.type === 'modification').length,
            removals: diffBlocks.filter((b) => b.type === 'removal').length,
          })}
        </p>
      </div>
    </section>
  )
}

/* ===== Sub-components ===== */

interface DiffPanelProps {
  title: string
  panelId: string
  contentLabel: string
  noMotion: boolean
  accentColor?: string
  children: React.ReactNode
}

function DiffPanel({ title, panelId, contentLabel, noMotion, accentColor, children }: DiffPanelProps) {
  return (
    <motion.article
      id={panelId}
      initial={noMotion ? undefined : { opacity: 0, y: 16 }}
      animate={noMotion ? undefined : { opacity: 1, y: 0 }}
      transition={noMotion ? undefined : { type: 'spring', stiffness: 300, damping: 25 }}
      className="flex flex-col overflow-hidden rounded-2xl glass"
    >
      <header
        className="border-b border-[var(--color-border)] px-4 py-3 flex items-center gap-2"
        style={accentColor ? { borderBottomColor: accentColor } : undefined}
      >
        {accentColor && (
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: accentColor }}
            aria-hidden="true"
          />
        )}
        <h3 className="text-sm font-semibold text-[var(--color-text)]">{title}</h3>
      </header>
      <div
        className="flex-1 overflow-auto p-4 space-y-3 max-h-[480px] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--color-primary)]"
        aria-label={contentLabel}
        tabIndex={0}
      >
        {children}
      </div>
    </motion.article>
  )
}

interface ContentBlock {
  type: 'unchanged' | 'addition' | 'modification' | 'removal'
  label: string
  text: string
  originalText?: string
}

function DiffBlock({ block, side }: { block: ContentBlock; side: 'standard' | 'adapted' }) {
  if (side === 'standard') {
    const isRemoved = block.type === 'removal'
    const isModified = block.type === 'modification'
    return (
      <div className={cn(
        'rounded-lg px-3 py-2 text-sm',
        isModified && 'bg-[var(--color-warning)]/8 border-l-2 border-[var(--color-warning)]',
      )}>
        <p className="text-xs font-semibold text-[var(--color-muted)] mb-0.5">{block.label}</p>
        <p className={cn(
          'text-[var(--color-text)]',
          isRemoved && 'line-through opacity-60',
        )}>
          {block.originalText ?? block.text}
        </p>
      </div>
    )
  }

  // Adapted side
  const bgClass =
    block.type === 'addition'
      ? 'bg-[var(--color-success)]/8 border-l-2 border-[var(--color-success)]'
      : block.type === 'modification'
        ? 'bg-[var(--color-warning)]/8 border-l-2 border-[var(--color-warning)]'
        : block.type === 'removal'
          ? 'bg-[var(--color-error)]/5 border-l-2 border-[var(--color-error)]/40'
          : ''

  return (
    <div className={cn('rounded-lg px-3 py-2 text-sm', bgClass)}>
      <div className="flex items-center gap-2 mb-0.5">
        <p className="text-xs font-semibold text-[var(--color-muted)]">{block.label}</p>
        {block.type !== 'unchanged' && (
          <span className={cn(
            'text-[10px] font-bold uppercase px-1.5 py-0.5 rounded',
            block.type === 'addition' && 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
            block.type === 'modification' && 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
            block.type === 'removal' && 'bg-[var(--color-error)]/15 text-[var(--color-error)]',
          )}>
            {block.type === 'addition' ? '+' : block.type === 'modification' ? '~' : '-'}
          </span>
        )}
      </div>
      <p className={cn(
        'text-[var(--color-text)]',
        block.type === 'removal' && 'line-through opacity-50',
      )}>
        {block.text}
      </p>
    </div>
  )
}

/* ===== Data helpers ===== */

function buildStandardContent(plan: StudyPlan): ContentBlock[] {
  const blocks: ContentBlock[] = []

  plan.objectives.forEach((obj, i) => {
    blocks.push({ type: 'unchanged', label: `Objective ${i + 1}`, text: obj })
  })

  plan.activities.forEach((act) => {
    blocks.push({
      type: 'unchanged',
      label: act.title,
      text: `${act.description} (${act.duration_minutes} min)`,
    })
  })

  plan.assessments.forEach((assess) => {
    blocks.push({
      type: 'unchanged',
      label: assess.title,
      text: `${assess.type}: ${assess.criteria.join(', ')}`,
    })
  })

  return blocks
}

function buildAdaptedContent(plan: StudyPlan, profile: DiffProfile): ContentBlock[] {
  if (profile === 'standard') return buildStandardContent(plan)

  const blocks: ContentBlock[] = []
  const profileMap: Record<string, string> = {
    tea: 'asd',
    tdah: 'adhd',
    dyslexia: 'dyslexia',
    hearing: 'hearing',
  }
  const profileKey = profileMap[profile] ?? profile

  plan.objectives.forEach((obj, i) => {
    blocks.push({ type: 'unchanged', label: `Objective ${i + 1}`, text: obj })
  })

  plan.activities.forEach((act) => {
    const adaptation = findAdaptation(act.adaptations, profileKey)
    if (adaptation) {
      blocks.push({
        type: 'modification',
        label: act.title,
        text: `${adaptation.description} (${act.duration_minutes} min)`,
        originalText: `${act.description} (${act.duration_minutes} min)`,
      })
    } else {
      blocks.push({
        type: 'unchanged',
        label: act.title,
        text: `${act.description} (${act.duration_minutes} min)`,
      })
    }
  })

  // Add accessibility notes as additions
  plan.accessibility_notes.forEach((note) => {
    if (note.toLowerCase().includes(profileKey) || plan.accessibility_notes.length <= 3) {
      blocks.push({ type: 'addition', label: 'Accessibility Note', text: note })
    }
  })

  plan.assessments.forEach((assess) => {
    const adaptation = findAdaptation(assess.adaptations, profileKey)
    if (adaptation) {
      blocks.push({
        type: 'modification',
        label: assess.title,
        text: `${adaptation.description}`,
        originalText: `${assess.type}: ${assess.criteria.join(', ')}`,
      })
    } else {
      blocks.push({
        type: 'unchanged',
        label: assess.title,
        text: `${assess.type}: ${assess.criteria.join(', ')}`,
      })
    }
  })

  return blocks
}

function findAdaptation(adaptations: Adaptation[], profile: string): Adaptation | undefined {
  return adaptations.find(
    (a) => a.profile.toLowerCase().includes(profile.toLowerCase()),
  )
}

function computeDiffBlocks(standard: ContentBlock[], adapted: ContentBlock[]): ContentBlock[] {
  // The adapted content already has diff types assigned
  return adapted
}
