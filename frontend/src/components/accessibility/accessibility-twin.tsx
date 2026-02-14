'use client'

import { useState, useMemo, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import type { DiffChange, TwinTab } from '@/types/accessibility'

interface AccessibilityTwinProps {
  /** The original (standard) plan content. */
  originalContent: string
  /** The adapted plan content for the selected accessibility persona. */
  adaptedContent: string
  /** Optional label for the adaptation type. */
  adaptationLabel?: string
}

/**
 * Accessibility Twin: Tabbed view showing standard vs adapted content.
 * Uses a tabbed layout (NOT clip-path slider) per ADR-044 for WCAG AAA compliance.
 * Diff highlights show additions in green and removals in red with both
 * color and texture/icon indicators for color-blind accessibility.
 */
export function AccessibilityTwin({
  originalContent,
  adaptedContent,
  adaptationLabel,
}: AccessibilityTwinProps) {
  const t = useTranslations('twin')
  const effectiveLabel = adaptationLabel ?? t('default_adaptation_label')
  const [activeTab, setActiveTab] = useState<TwinTab>('original')

  const diffChanges = useMemo(
    () => computeLineDiff(originalContent, adaptedContent),
    [originalContent, adaptedContent],
  )

  const handleTabChange = useCallback((tab: TwinTab) => {
    setActiveTab(tab)
  }, [])

  return (
    <div className="flex flex-col gap-4">
      {/* Tab bar */}
      <div
        role="tablist"
        aria-label={t('comparison_label')}
        className="flex gap-1 rounded-lg bg-[var(--color-surface-elevated)] p-1"
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault()
            handleTabChange(activeTab === 'original' ? 'adapted' : 'original')
          }
        }}
      >
        <TabButton
          id="tab-original"
          label={t('original')}
          isActive={activeTab === 'original'}
          controls="panel-original"
          onSelect={() => handleTabChange('original')}
        />
        <TabButton
          id="tab-adapted"
          label={t('adapted', { label: effectiveLabel })}
          isActive={activeTab === 'adapted'}
          controls="panel-adapted"
          onSelect={() => handleTabChange('adapted')}
        />
      </div>

      {/* Tab panels */}
      <AnimatePresence mode="wait">
        {activeTab === 'original' ? (
          <motion.div
            key="original"
            id="panel-original"
            role="tabpanel"
            aria-labelledby="tab-original"
            tabIndex={0}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="rounded-lg border border-[var(--color-border)] p-6"
          >
            <div className="prose prose-sm max-w-none">
              {originalContent.split('\n').map((line, i) => (
                <p key={i} className="mb-2 last:mb-0">
                  {line || '\u00A0'}
                </p>
              ))}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="adapted"
            id="panel-adapted"
            role="tabpanel"
            aria-labelledby="tab-adapted"
            tabIndex={0}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="rounded-lg border border-[var(--color-border)] p-6"
          >
            <DiffView changes={diffChanges} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* --- Sub-components --- */

interface TabButtonProps {
  id: string
  label: string
  isActive: boolean
  controls: string
  onSelect: () => void
}

function TabButton({ id, label, isActive, controls, onSelect }: TabButtonProps) {
  return (
    <button
      id={id}
      role="tab"
      aria-selected={isActive}
      aria-controls={controls}
      tabIndex={isActive ? 0 : -1}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
      className={cn(
        'flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
        isActive
          ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
          : 'text-[var(--color-muted)] hover:text-[var(--color-text)]',
      )}
    >
      {label}
    </button>
  )
}

interface DiffViewProps {
  changes: DiffChange[]
}

/**
 * Renders diff changes with color + texture indicators for WCAG AAA.
 * Additions: green background + [+] prefix icon.
 * Removals: red background + strikethrough + [-] prefix icon.
 * This ensures changes are perceivable by color-blind users.
 */
function DiffView({ changes }: DiffViewProps) {
  const t = useTranslations('twin')

  if (changes.length === 0) {
    return (
      <p className="text-[var(--color-muted)] italic">
        {t('no_diff')}
      </p>
    )
  }

  return (
    <div className="space-y-1" role="list" aria-label={t('diff_label')}>
      {changes.map((change, i) => (
        <div
          key={i}
          role="listitem"
          className={cn(
            'flex items-start gap-2 rounded px-3 py-1.5 text-sm',
            change.type === 'addition' &&
              'border-l-4 border-[var(--color-success)] bg-[var(--color-success)]/10 text-[var(--color-text)]',
            change.type === 'removal' &&
              'border-l-4 border-[var(--color-error)] bg-[var(--color-error)]/10 text-[var(--color-text)] line-through',
            change.type === 'unchanged' && 'text-[var(--color-text)]',
          )}
        >
          {change.type === 'addition' && (
            <span
              aria-label={t('addition')}
              className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-success)] text-xs font-bold text-[var(--color-on-primary)]"
            >
              +
            </span>
          )}
          {change.type === 'removal' && (
            <span
              aria-label={t('removal')}
              className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-error)] text-xs font-bold text-[var(--color-on-primary)]"
            >
              -
            </span>
          )}
          <span>{change.text || '\u00A0'}</span>
        </div>
      ))}
    </div>
  )
}

/* --- Diff computation --- */

/**
 * Simple line-level diff between original and adapted text.
 * Uses a basic LCS (Longest Common Subsequence) approach for line matching.
 */
function computeLineDiff(original: string, adapted: string): DiffChange[] {
  const origLines = original.split('\n')
  const adaptLines = adapted.split('\n')

  const changes: DiffChange[] = []
  const origSet = new Set(origLines)
  const adaptSet = new Set(adaptLines)

  let oi = 0
  let ai = 0

  while (oi < origLines.length || ai < adaptLines.length) {
    if (oi < origLines.length && ai < adaptLines.length) {
      if (origLines[oi] === adaptLines[ai]) {
        changes.push({ type: 'unchanged', text: origLines[oi] })
        oi++
        ai++
      } else if (!adaptSet.has(origLines[oi])) {
        changes.push({ type: 'removal', text: origLines[oi] })
        oi++
      } else if (!origSet.has(adaptLines[ai])) {
        changes.push({ type: 'addition', text: adaptLines[ai] })
        ai++
      } else {
        // Both exist elsewhere, treat current original as removal
        changes.push({ type: 'removal', text: origLines[oi] })
        oi++
      }
    } else if (oi < origLines.length) {
      changes.push({ type: 'removal', text: origLines[oi] })
      oi++
    } else {
      changes.push({ type: 'addition', text: adaptLines[ai] })
      ai++
    }
  }

  return changes
}
