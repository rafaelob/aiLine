'use client'

import DOMPurify from 'dompurify'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { toBionicHtml } from '@/lib/bionic-reading'

interface BionicTextProps {
  children: string
  as?: 'p' | 'span' | 'div'
  className?: string
}

/**
 * Renders text with Bionic Reading formatting when enabled.
 * Bolds the first half of each word to guide eye fixation.
 * Sanitizes output with DOMPurify to prevent XSS.
 */
export function BionicText({ children, as: Tag = 'p', className }: BionicTextProps) {
  const bionicMode = useAccessibilityStore((s) => s.bionicReading)

  if (!bionicMode) {
    return <Tag className={className}>{children}</Tag>
  }

  const html = DOMPurify.sanitize(toBionicHtml(children))
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
