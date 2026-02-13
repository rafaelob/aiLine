'use client'

import { useEffect, useRef, useState, useCallback, useId } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { loadMermaid } from '@/lib/mermaid-loader'
import { useThemeContext } from '@/hooks/use-theme-context'
import { Skeleton } from '@/components/ui/skeleton'

interface MermaidRendererProps {
  /** Raw Mermaid diagram code */
  code: string
  /** Optional CSS class for the outer wrapper */
  className?: string
}

const DARK_THEMES = new Set([
  'high-contrast',
  'screen-reader',
])

/**
 * Client-side Mermaid.js renderer with theme awareness.
 * Dynamically imports mermaid to avoid SSR issues.
 * Supports collapsible panel, copy-to-clipboard, and fullscreen.
 */
export function MermaidRenderer({ code, className }: MermaidRendererProps) {
  const t = useTranslations('mermaid')
  const theme = useThemeContext()
  const containerId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const dialogRef = useRef<HTMLDialogElement>(null)

  const [svg, setSvg] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const [copied, setCopied] = useState(false)

  const isDark = DARK_THEMES.has(theme)
  const mermaidTheme = isDark ? 'dark' : 'default'

  // Render mermaid diagram whenever code or theme changes
  useEffect(() => {
    let cancelled = false

    async function renderDiagram() {
      setLoading(true)
      setError(null)

      try {
        const mermaid = await loadMermaid()
        mermaid.initialize({
          startOnLoad: false,
          theme: mermaidTheme,
          securityLevel: 'strict',
          fontFamily: 'inherit',
        })

        // Use a unique ID for rendering
        const renderContainerId = `mermaid-${containerId.replace(/:/g, '')}`
        const { svg: renderedSvg } = await mermaid.render(
          renderContainerId,
          code.trim()
        )

        if (!cancelled) {
          setSvg(renderedSvg)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : t('render_error')
          )
          setLoading(false)
        }
      }
    }

    renderDiagram()

    return () => {
      cancelled = true
    }
  }, [code, mermaidTheme, containerId])

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: no-op if clipboard API unavailable
    }
  }, [code])

  const handleFullscreen = useCallback(() => {
    dialogRef.current?.showModal()
  }, [])

  const handleCloseFullscreen = useCallback(() => {
    dialogRef.current?.close()
  }, [])

  return (
    <div className={cn('mt-4', className)}>
      {/* Collapsible header */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        aria-expanded={!collapsed}
        className={cn(
          'flex items-center gap-2 w-full text-left',
          'px-4 py-3 rounded-t-[var(--radius-md)]',
          'bg-[var(--color-surface-elevated)] border border-[var(--color-border)]',
          'text-sm font-medium text-[var(--color-text)]',
          'hover:bg-[var(--color-surface)] transition-colors',
          collapsed && 'rounded-b-[var(--radius-md)]'
        )}
      >
        <ChevronIcon collapsed={collapsed} />
        <DiagramIcon />
        <span>{t('visual_explanation')}</span>
      </button>

      {/* Diagram panel */}
      {!collapsed && (
        <div
          ref={containerRef}
          className={cn(
            'border border-t-0 border-[var(--color-border)]',
            'rounded-b-[var(--radius-md)]',
            'bg-[var(--color-surface)]'
          )}
        >
          {/* Toolbar */}
          <div className="flex items-center justify-end gap-2 px-3 py-2 border-b border-[var(--color-border)]">
            <button
              type="button"
              onClick={handleCopy}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium',
                'rounded-[var(--radius-sm)]',
                'text-[var(--color-muted)] hover:text-[var(--color-text)]',
                'hover:bg-[var(--color-surface-elevated)] transition-colors'
              )}
              aria-label={t('copy_code')}
            >
              {copied ? <CheckIcon /> : <CopyIcon />}
              {copied ? t('copied') : t('copy_code')}
            </button>
            <button
              type="button"
              onClick={handleFullscreen}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium',
                'rounded-[var(--radius-sm)]',
                'text-[var(--color-muted)] hover:text-[var(--color-text)]',
                'hover:bg-[var(--color-surface-elevated)] transition-colors'
              )}
              aria-label={t('fullscreen')}
            >
              <FullscreenIcon />
              {t('fullscreen')}
            </button>
          </div>

          {/* Content area */}
          <div className="p-4 overflow-x-auto">
            {loading && (
              <div aria-label={t('loading')} role="status">
                <Skeleton className="h-40 w-full" />
              </div>
            )}

            {error && (
              <div
                role="alert"
                className={cn(
                  'p-4 rounded-[var(--radius-md)] text-sm',
                  'bg-[var(--color-error)]/10 text-[var(--color-error)]'
                )}
              >
                {t('render_error')}: {error}
              </div>
            )}

            {!loading && !error && svg && (
              <div
                className="mermaid-output flex justify-center"
                dangerouslySetInnerHTML={{ __html: svg }}
                role="img"
                aria-label={t('diagram_alt')}
              />
            )}
          </div>
        </div>
      )}

      {/* Fullscreen dialog */}
      <dialog
        ref={dialogRef}
        className={cn(
          'w-[90vw] max-w-5xl max-h-[90vh] p-0 rounded-[var(--radius-lg)]',
          'bg-[var(--color-surface)] border border-[var(--color-border)]',
          'backdrop:bg-black/50'
        )}
        aria-label={t('fullscreen_diagram')}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <span className="text-sm font-semibold text-[var(--color-text)]">
            {t('visual_explanation')}
          </span>
          <button
            type="button"
            onClick={handleCloseFullscreen}
            className={cn(
              'p-2 rounded-[var(--radius-sm)]',
              'text-[var(--color-muted)] hover:text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)] transition-colors'
            )}
            aria-label={t('close_fullscreen')}
          >
            <CloseIcon />
          </button>
        </div>
        <div className="p-6 overflow-auto max-h-[calc(90vh-5rem)]">
          {svg && (
            <div
              className="mermaid-output flex justify-center"
              dangerouslySetInnerHTML={{ __html: svg }}
              role="img"
              aria-label={t('diagram_alt')}
            />
          )}
        </div>
      </dialog>
    </div>
  )
}

/**
 * Utility: extracts mermaid code blocks from markdown text.
 * Returns an array of {before, mermaidCode, after} segments for rendering.
 */
export function extractMermaidBlocks(
  text: string
): Array<{ type: 'text'; content: string } | { type: 'mermaid'; content: string }> {
  const pattern = /```mermaid\n([\s\S]*?)```/g
  const segments: Array<
    { type: 'text'; content: string } | { type: 'mermaid'; content: string }
  > = []

  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text)) !== null) {
    // Text before the code block
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    // The mermaid code block
    segments.push({ type: 'mermaid', content: match[1] })
    lastIndex = match.index + match[0].length
  }

  // Remaining text after last code block
  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return segments
}

/* ===== Icons ===== */

function ChevronIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn('transition-transform', collapsed ? '-rotate-90' : 'rotate-0')}
    >
      <polyline points="4 6 8 10 12 6" />
    </svg>
  )
}

function DiagramIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="8" y="14" width="7" height="7" rx="1" />
      <line x1="6.5" y1="10" x2="11.5" y2="14" />
      <line x1="17.5" y1="10" x2="12.5" y2="14" />
    </svg>
  )
}

function CopyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function FullscreenIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}
