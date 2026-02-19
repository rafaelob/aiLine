'use client'

import { useMemo, useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

interface BraillePreviewProps {
  /** BRF text content to display. */
  brf: string
  /** Language of the BRF content for the lang attribute. Defaults to 'en'. */
  lang?: string
  /** Optional filename for BRF download (without extension). Defaults to 'export'. */
  filename?: string
  /** Optional CSS class. */
  className?: string
}

/** Standard BRF line width (cells per line). */
const BRF_LINE_WIDTH = 40
/** Standard BRF page height (lines per page). */
const BRF_PAGE_HEIGHT = 25

/**
 * Braille preview panel that renders BRF text in a monospace layout.
 * Shows translation statistics (characters, lines, pages) and allows
 * page-by-page navigation for long content.
 *
 * Accessible: proper ARIA labels, keyboard-operable page navigation.
 */
export function BraillePreview({ brf, lang = 'en', filename = 'export', className }: BraillePreviewProps) {
  const t = useTranslations('braille')
  const [currentPage, setCurrentPage] = useState(0)
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle')

  const stats = useMemo(() => {
    const chars = brf.length
    const lines = brf.split(/\r?\n/).length
    const pages = Math.max(1, Math.ceil(lines / BRF_PAGE_HEIGHT))
    return { chars, lines, pages }
  }, [brf])

  const pages = useMemo(() => {
    const allLines = brf.split(/\r?\n/)
    const result: string[][] = []
    for (let i = 0; i < allLines.length; i += BRF_PAGE_HEIGHT) {
      result.push(allLines.slice(i, i + BRF_PAGE_HEIGHT))
    }
    if (result.length === 0) result.push([''])
    return result
  }, [brf])

  const currentPageLines = pages[currentPage] ?? pages[0]

  const goToPrev = useCallback(() => {
    setCurrentPage((p) => Math.max(0, p - 1))
  }, [])

  const goToNext = useCallback(() => {
    setCurrentPage((p) => Math.min(pages.length - 1, p + 1))
  }, [pages.length])

  const handleDownload = useCallback(() => {
    const blob = new Blob([brf], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}.brf`
    a.click()
    URL.revokeObjectURL(url)
  }, [brf, filename])

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(brf)
      setCopyState('copied')
      setTimeout(() => setCopyState('idle'), 2000)
    } catch {
      setCopyState('error')
      setTimeout(() => setCopyState('idle'), 2000)
    }
  }, [brf])

  return (
    <div
      className={cn('flex flex-col gap-3', className)}
      role="region"
      aria-label={t('preview_label')}
    >
      {/* Stats bar + actions */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--color-muted)]">
          <span>
            <span className="font-medium text-[var(--color-text)]">{stats.chars.toLocaleString()}</span>{' '}
            {t('stat_chars')}
          </span>
          <span aria-hidden="true" className="w-px h-3 bg-[var(--color-border)]" />
          <span>
            <span className="font-medium text-[var(--color-text)]">{stats.lines}</span>{' '}
            {t('stat_lines')}
          </span>
          <span aria-hidden="true" className="w-px h-3 bg-[var(--color-border)]" />
          <span>
            <span className="font-medium text-[var(--color-text)]">{stats.pages}</span>{' '}
            {t('stat_pages')}
          </span>
          <span aria-hidden="true" className="w-px h-3 bg-[var(--color-border)]" />
          <span>
            {BRF_LINE_WIDTH} {t('stat_cells_per_line')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className={cn(
              'rounded-[var(--radius-md)] px-3 py-1.5',
              'text-xs font-medium text-[var(--color-text)]',
              'border border-[var(--color-border)]',
              'hover:bg-[var(--color-surface-elevated)] transition-colors',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
            )}
            aria-label={t('copy_label')}
          >
            {copyState === 'copied' ? t('copied') : copyState === 'error' ? t('copy_error') : t('copy')}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className={cn(
              'rounded-[var(--radius-md)] px-3 py-1.5',
              'text-xs font-medium text-white',
              'bg-[var(--color-primary)] hover:bg-[var(--color-primary)]/90',
              'transition-colors',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
            )}
            aria-label={t('download_label')}
          >
            <DownloadIcon />
            <span className="ml-1">{t('download')}</span>
          </button>
        </div>
      </div>

      {/* BRF content display */}
      <div
        className={cn(
          'overflow-auto rounded-[var(--radius-md)] p-4',
          'border border-[var(--color-border)]',
          'bg-[var(--color-surface-elevated)]',
          'font-mono text-sm leading-relaxed',
          'text-[var(--color-text)]',
          'min-h-[200px] max-h-[400px]',
          'focus-visible:outline-2 focus-visible:outline-offset-2',
          'focus-visible:outline-[var(--color-primary)]',
        )}
        tabIndex={0}
        role="document"
        lang={lang}
        aria-label={t('content_label', { page: currentPage + 1, total: stats.pages })}
        aria-roledescription={t('braille_document')}
        aria-live="polite"
        aria-atomic="true"
      >
        <pre className="whitespace-pre-wrap break-all" style={{ maxWidth: `${BRF_LINE_WIDTH}ch` }}>
          {currentPageLines.join('\n')}
        </pre>
      </div>

      {/* Page navigation */}
      {stats.pages > 1 && (
        <nav
          className="flex items-center justify-between"
          aria-label={t('page_nav_label')}
        >
          <button
            type="button"
            onClick={goToPrev}
            disabled={currentPage === 0}
            className={cn(
              'rounded-[var(--radius-md)] px-3 py-1.5',
              'text-xs font-medium text-[var(--color-text)]',
              'border border-[var(--color-border)]',
              'hover:bg-[var(--color-surface-elevated)] transition-colors',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'disabled:opacity-40 disabled:cursor-not-allowed',
            )}
            aria-label={t('prev_page')}
          >
            {t('prev')}
          </button>
          <span className="text-xs text-[var(--color-muted)]" aria-live="polite" aria-atomic="true">
            {t('page_indicator', { current: currentPage + 1, total: stats.pages })}
          </span>
          <button
            type="button"
            onClick={goToNext}
            disabled={currentPage === stats.pages - 1}
            className={cn(
              'rounded-[var(--radius-md)] px-3 py-1.5',
              'text-xs font-medium text-[var(--color-text)]',
              'border border-[var(--color-border)]',
              'hover:bg-[var(--color-surface-elevated)] transition-colors',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'disabled:opacity-40 disabled:cursor-not-allowed',
            )}
            aria-label={t('next_page')}
          >
            {t('next')}
          </button>
        </nav>
      )}
    </div>
  )
}

function DownloadIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="inline-block"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}
