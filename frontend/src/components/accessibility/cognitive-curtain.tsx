'use client'

import { useAccessibilityStore } from '@/stores/accessibility-store'

/**
 * Cognitive Curtain (Focus Mode) for students with ADHD/sensory processing.
 * Dims header, nav, aside, and footer so only main content is prominent.
 * Injects global CSS when focusMode is active; the body class is managed by the store.
 */
export function CognitiveCurtain() {
  const focusMode = useAccessibilityStore((s) => s.focusMode)

  if (!focusMode) return null

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `
      .cognitive-curtain-active header,
      .cognitive-curtain-active nav,
      .cognitive-curtain-active aside,
      .cognitive-curtain-active footer {
        opacity: 0.15;
        transition: opacity 0.3s ease;
      }
      .cognitive-curtain-active header:hover,
      .cognitive-curtain-active header:focus-within,
      .cognitive-curtain-active nav:hover,
      .cognitive-curtain-active nav:focus-within,
      .cognitive-curtain-active aside:hover,
      .cognitive-curtain-active aside:focus-within,
      .cognitive-curtain-active footer:hover,
      .cognitive-curtain-active footer:focus-within {
        opacity: 0.85;
      }
      .cognitive-curtain-active main {
        position: relative;
        z-index: 10;
      }
      @media (prefers-reduced-motion: reduce) {
        .cognitive-curtain-active header,
        .cognitive-curtain-active nav,
        .cognitive-curtain-active aside,
        .cognitive-curtain-active footer {
          transition: none;
        }
      }
    `,
      }}
    />
  )
}
