'use client'

import { useState, useMemo, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import DOMPurify from 'dompurify'
import { cn } from '@/lib/cn'
import { EXPORT_VARIANTS } from '@/lib/accessibility-data'
import type { ExportVariant } from '@/types/accessibility'

interface ExportViewerProps {
  /** Map of variant id to HTML content string. */
  exports: Record<string, string>
  /** Whether to show in full-screen preview mode. */
  fullScreen?: boolean
  /** Callback when full-screen mode is toggled. */
  onFullScreenToggle?: () => void
}

/**
 * Side-by-side comparison of standard vs adapted plan exports.
 * Left panel: standard export. Right panel: selected accessibility variant.
 * HTML content is sanitized with DOMPurify (ADR-046) before rendering.
 */
export function ExportViewer({
  exports,
  fullScreen = false,
  onFullScreenToggle,
}: ExportViewerProps) {
  const t = useTranslations('export_viewer')
  const tv = useTranslations('export_variants')
  const [selectedVariant, setSelectedVariant] = useState<ExportVariant>('low_distraction')

  const standardHtml = useMemo(
    () => sanitize(exports['standard'] ?? ''),
    [exports],
  )

  const variantHtml = useMemo(
    () => sanitize(exports[selectedVariant] ?? ''),
    [exports, selectedVariant],
  )

  const availableVariants = useMemo(
    () => EXPORT_VARIANTS.filter((v) => v.id !== 'standard' && exports[v.id]),
    [exports],
  )

  const selectedVariantLabel = useMemo(() => {
    const found = availableVariants.find((v) => v.id === selectedVariant)
    return found ? tv(found.label) : t('variant_fallback')
  }, [availableVariants, selectedVariant, tv, t])

  const handleVariantChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setSelectedVariant(e.target.value as ExportVariant)
    },
    [],
  )

  return (
    <div
      className={cn(
        'flex flex-col gap-4',
        fullScreen && 'fixed inset-0 z-50 bg-[var(--color-bg)] p-6',
      )}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between glass rounded-xl p-3">
        <div className="flex items-center gap-3">
          <label
            htmlFor="variant-select"
            className="text-sm font-medium text-[var(--color-text)]"
          >
            {t('variant_label')}
          </label>
          <select
            id="variant-select"
            value={selectedVariant}
            onChange={handleVariantChange}
            className={cn(
              'rounded-lg glass px-3 py-2 text-sm text-[var(--color-text)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
            )}
            aria-label={t('variant_aria')}
          >
            {availableVariants.map((v) => (
              <option key={v.id} value={v.id}>
                {tv(v.label)}
              </option>
            ))}
          </select>
        </div>

        {onFullScreenToggle && (
          <button
            onClick={onFullScreenToggle}
            className={cn(
              'rounded-lg glass px-3 py-2 text-sm font-medium text-[var(--color-text)]',
              'hover:bg-[var(--color-surface)] focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)] transition-colors',
            )}
            aria-label={fullScreen ? t('fullscreen_exit_label') : t('fullscreen_enter_label')}
          >
            {fullScreen ? t('fullscreen_exit') : t('fullscreen_enter')}
          </button>
        )}
      </div>

      {/* Side-by-side panels */}
      <div
        className="grid flex-1 gap-4 md:grid-cols-2"
        role="region"
        aria-label={t('comparison_label')}
      >
        <ExportPanel
          title={t('standard_panel')}
          html={standardHtml}
          panelId="standard-panel"
          contentLabel={t('content_label', { title: t('standard_panel') })}
          noContentLabel={t('no_content')}
        />
        <ExportPanel
          title={selectedVariantLabel}
          html={variantHtml}
          panelId="variant-panel"
          contentLabel={t('content_label', { title: selectedVariantLabel })}
          noContentLabel={t('no_content')}
        />
      </div>
    </div>
  )
}

/* --- Sub-component --- */

interface ExportPanelProps {
  title: string
  html: string
  panelId: string
  contentLabel: string
  noContentLabel: string
}

function ExportPanel({ title, html, panelId, contentLabel, noContentLabel }: ExportPanelProps) {
  return (
    <motion.article
      id={panelId}
      layoutId={`export-panel-${panelId}`}
      initial={{ opacity: 0, rotateY: -8 }}
      animate={{ opacity: 1, rotateY: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="flex flex-col overflow-hidden rounded-2xl glass card-hover"
      style={{ perspective: '800px', transformStyle: 'preserve-3d' }}
    >
      <header className="border-b border-[var(--color-border)] glass px-4 py-3">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">
          {title}
        </h3>
      </header>
      <div
        className="flex-1 overflow-auto p-4"
        role="document"
        aria-label={contentLabel}
        tabIndex={0}
      >
        {html ? (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <p className="text-sm text-[var(--color-muted)] italic text-center py-8">
            {noContentLabel}
          </p>
        )}
      </div>
    </motion.article>
  )
}

/* --- Helpers --- */

/**
 * Sanitize HTML using DOMPurify (ADR-046).
 * Allows safe structural HTML while stripping XSS vectors.
 */
function sanitize(html: string): string {
  if (!html) return ''
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'br', 'hr',
      'ul', 'ol', 'li',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'strong', 'em', 'u', 'mark', 'del', 'ins',
      'blockquote', 'pre', 'code',
      'div', 'span', 'section', 'article',
      'img', 'figure', 'figcaption',
    ],
    ALLOWED_ATTR: ['class', 'id', 'alt', 'src', 'title', 'aria-label', 'role'],
  })
}
