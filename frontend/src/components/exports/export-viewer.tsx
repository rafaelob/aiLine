'use client'

import { useState, useMemo, useCallback } from 'react'
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
        fullScreen && 'fixed inset-0 z-50 bg-white p-6 dark:bg-gray-900',
      )}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <label
            htmlFor="variant-select"
            className="text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Variante de acessibilidade:
          </label>
          <select
            id="variant-select"
            value={selectedVariant}
            onChange={handleVariantChange}
            className={cn(
              'rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600',
              'dark:border-gray-600 dark:bg-gray-800 dark:text-white',
            )}
            aria-label="Selecionar variante de exportação acessível"
          >
            {availableVariants.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </select>
        </div>

        {onFullScreenToggle && (
          <button
            onClick={onFullScreenToggle}
            className={cn(
              'rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium',
              'hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-blue-600 transition-colors',
              'dark:border-gray-600 dark:hover:bg-gray-800 dark:text-gray-300',
            )}
            aria-label={fullScreen ? 'Sair da tela cheia' : 'Visualizar em tela cheia'}
          >
            {fullScreen ? 'Sair da Tela Cheia' : 'Tela Cheia'}
          </button>
        )}
      </div>

      {/* Side-by-side panels */}
      <div
        className="grid flex-1 gap-4 md:grid-cols-2"
        role="region"
        aria-label="Comparação de exportações"
      >
        <ExportPanel
          title="Versão Padrão"
          html={standardHtml}
          panelId="standard-panel"
        />
        <ExportPanel
          title={
            availableVariants.find((v) => v.id === selectedVariant)?.label ??
            'Variante'
          }
          html={variantHtml}
          panelId="variant-panel"
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
}

function ExportPanel({ title, html, panelId }: ExportPanelProps) {
  return (
    <article
      id={panelId}
      className="flex flex-col overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700"
    >
      <header className="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {title}
        </h3>
      </header>
      <div
        className="flex-1 overflow-auto p-4"
        role="document"
        aria-label={`Conteúdo da exportação: ${title}`}
        tabIndex={0}
      >
        {html ? (
          <div
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <p className="text-sm text-gray-400 italic dark:text-gray-500">
            Nenhum conteúdo disponível para esta variante.
          </p>
        )}
      </div>
    </article>
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
