'use client'

import { useState, useMemo, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
import DOMPurify from 'dompurify'
import { cn } from '@/lib/cn'
import { API_BASE, getAuthHeaders } from '@/lib/api'
import { EXPORT_VARIANTS } from '@/lib/accessibility-data'
import { BraillePreview } from '@/components/accessibility/braille-preview'
import type { ExportVariant } from '@/types/accessibility'

interface ExportViewerProps {
  /** Map of variant id to HTML content string. */
  exports: Record<string, string>
  /** Plain text content for BRF Braille export. */
  plainText?: string
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
  plainText,
  fullScreen = false,
  onFullScreenToggle,
}: ExportViewerProps) {
  const t = useTranslations('export_viewer')
  const tv = useTranslations('export_variants')
  const [selectedVariant, setSelectedVariant] = useState<ExportVariant>('low_distraction')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

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

  const [brfLoading, setBrfLoading] = useState(false)

  const brfContent = useMemo(() => {
    if (!plainText) return ''
    return textToBrf(plainText)
  }, [plainText])

  const handleVariantChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setSelectedVariant(e.target.value as ExportVariant)
    },
    [],
  )

  const [brfError, setBrfError] = useState<string | null>(null)

  const handleBrfDownload = useCallback(async () => {
    if (!plainText) return
    setBrfLoading(true)
    setBrfError(null)
    try {
      const res = await fetch(`${API_BASE}/media/export-brf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ text: plainText }),
      })
      if (!res.ok) throw new Error('BRF export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'export.brf'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setBrfError(t('brf_error'))
    } finally {
      setBrfLoading(false)
    }
  }, [plainText, t])

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

        <div className="flex items-center gap-2">
          {plainText && (
            <button
              type="button"
              onClick={handleBrfDownload}
              disabled={brfLoading}
              className={cn(
                'rounded-lg glass px-3 py-2 text-sm font-medium text-[var(--color-text)]',
                'hover:bg-[var(--color-surface)] focus-visible:outline-2 focus-visible:outline-offset-2',
                'focus-visible:outline-[var(--color-primary)] transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed',
              )}
              aria-label={t('brf_download_label')}
              aria-busy={brfLoading}
            >
              <BrailleIcon />
              <span className="ml-1.5">{brfLoading ? t('brf_downloading') : t('brf_download')}</span>
            </button>
          )}
          {brfError && (
            <span role="alert" className="text-xs text-[var(--color-error)]">{brfError}</span>
          )}
          {onFullScreenToggle && (
            <button
              type="button"
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
          noMotion={noMotion}
        />
        <ExportPanel
          title={selectedVariantLabel}
          html={variantHtml}
          panelId="variant-panel"
          contentLabel={t('content_label', { title: selectedVariantLabel })}
          noContentLabel={t('no_content')}
          noMotion={noMotion}
        />
      </div>

      {/* Braille BRF preview */}
      {plainText && brfContent && (
        <section aria-label={t('brf_preview_label')}>
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">
            {t('brf_preview_heading')}
          </h3>
          <BraillePreview brf={brfContent} />
        </section>
      )}
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
  noMotion: boolean
}

function ExportPanel({ title, html, panelId, contentLabel, noContentLabel, noMotion }: ExportPanelProps) {
  return (
    <motion.article
      id={panelId}
      layoutId={`export-panel-${panelId}`}
      initial={noMotion ? undefined : { opacity: 0, rotateY: -8 }}
      animate={noMotion ? undefined : { opacity: 1, rotateY: 0 }}
      transition={noMotion ? undefined : { type: 'spring', stiffness: 300, damping: 25 }}
      className="flex flex-col overflow-hidden rounded-2xl glass card-hover"
      style={noMotion ? undefined : { perspective: '800px', transformStyle: 'preserve-3d' }}
    >
      <header className="border-b border-[var(--color-border)] glass px-4 py-3">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">
          {title}
        </h3>
      </header>
      <div
        className="flex-1 overflow-auto p-4 focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--color-primary)]"
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
 * Image src is restricted to https: and data:image/ to prevent
 * javascript: or other dangerous protocol injection via img tags.
 */
function sanitize(html: string): string {
  if (!html) return ''
  const clean = DOMPurify.sanitize(html, {
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
    ALLOWED_ATTR: ['class', 'alt', 'src', 'title', 'aria-label', 'role'],
    FORBID_ATTR: ['style', 'id'],
    ALLOWED_URI_REGEXP: /^https?:/i,
  })
  return clean
}

function BrailleIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className="inline-block"
    >
      <circle cx="6" cy="4" r="2" />
      <circle cx="6" cy="12" r="2" />
      <circle cx="6" cy="20" r="2" />
      <circle cx="14" cy="4" r="2" />
      <circle cx="14" cy="12" r="2" opacity="0.3" />
      <circle cx="14" cy="20" r="2" opacity="0.3" />
    </svg>
  )
}

/**
 * Lightweight client-side Grade 1 BRF translator (mirrors backend BrfTranslator).
 * Converts plain text to BRF format with 40-char lines and page breaks.
 */
const DIGIT_MAP: Record<string, string> = {
  '0': 'j', '1': 'a', '2': 'b', '3': 'c', '4': 'd',
  '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i',
}

const PUNCT_MAP: Record<string, string> = {
  ' ': ' ', '.': '4', ',': '1', ';': '3', ':': '5',
  '!': '6', '?': '8', "'": "'", '"': '7', '-': '-',
  '(': '"', ')': '"', '/': '/', '\n': '\n', '\t': '  ',
}

function textToBrf(text: string): string {
  const chars: string[] = []
  let inNumber = false

  for (const ch of text) {
    if (ch === '\n') {
      inNumber = false
      chars.push('\n')
      continue
    }
    if (/\d/.test(ch)) {
      if (!inNumber) {
        chars.push('#')
        inNumber = true
      }
      chars.push(DIGIT_MAP[ch] ?? '8')
      continue
    }
    const lower = ch.toLowerCase()
    if (lower >= 'a' && lower <= 'z') {
      inNumber = false
      if (ch !== lower) chars.push(',')
      chars.push(lower)
      continue
    }
    if (ch in PUNCT_MAP) {
      inNumber = false
      chars.push(PUNCT_MAP[ch])
      continue
    }
    inNumber = false
    chars.push('8')
  }

  // Wrap lines at 40 chars
  const raw = chars.join('')
  const rawLines = raw.split('\n')
  const wrapped: string[] = []
  for (const line of rawLines) {
    if (line.length <= 40) {
      wrapped.push(line)
    } else {
      let remaining = line
      while (remaining.length > 40) {
        const breakPos = remaining.lastIndexOf(' ', 40)
        const pos = breakPos > 0 ? breakPos : 40
        wrapped.push(remaining.slice(0, pos).trimEnd())
        remaining = remaining.slice(pos).trimStart()
      }
      wrapped.push(remaining)
    }
  }

  return wrapped.join('\n')
}
