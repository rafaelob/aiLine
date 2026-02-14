'use client'

import { lazy, Suspense } from 'react'
import { extractMermaidBlocks } from './mermaid-renderer'
import { SkeletonCard } from '@/components/ui/skeleton'

const MermaidRenderer = lazy(() => import('./mermaid-renderer'))

interface MarkdownWithMermaidProps {
  /** Text content that may contain ```mermaid code blocks */
  content: string
  /** CSS class for text segments */
  textClassName?: string
}

/**
 * Renders text content with embedded Mermaid diagram blocks.
 * Plain text is rendered as-is; ```mermaid blocks are rendered via MermaidRenderer.
 */
export function MarkdownWithMermaid({
  content,
  textClassName,
}: MarkdownWithMermaidProps) {
  const segments = extractMermaidBlocks(content)

  if (segments.length === 0) return null

  // If no mermaid blocks found, render as plain text
  if (segments.length === 1 && segments[0].type === 'text') {
    return <span className={textClassName}>{segments[0].content}</span>
  }

  return (
    <>
      {segments.map((segment, i) =>
        segment.type === 'mermaid' ? (
          <Suspense key={i} fallback={<SkeletonCard />}>
            <MermaidRenderer code={segment.content} />
          </Suspense>
        ) : (
          <span key={i} className={textClassName}>
            {segment.content}
          </span>
        )
      )}
    </>
  )
}
