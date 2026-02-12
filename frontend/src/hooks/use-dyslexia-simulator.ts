'use client'

import { useCallback, useEffect, useRef } from 'react'

/**
 * Dyslexia simulation hook.
 * Shuffles interior letters in words within the target element
 * to approximate the reading experience of someone with dyslexia.
 *
 * Based on the well-known demonstration that people can read words
 * as long as the first and last letters are in the correct position.
 * Dyslexic readers, however, struggle even with normal text --
 * this simulation creates a comparable difficulty for non-dyslexic readers.
 */
export function useDyslexiaSimulator(active: boolean) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const targetRef = useRef<HTMLElement | null>(null)

  /**
   * Capture text nodes and their original content from a DOM subtree.
   * Returns a snapshot array so we do not mutate the ref directly
   * inside useCallback (React Compiler immutability rule).
   */
  const captureTextNodes = useCallback((root: HTMLElement): TextNodeEntry[] => {
    const entries: TextNodeEntry[] = []
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
    let node = walker.nextNode()
    while (node) {
      if (node.textContent && node.textContent.trim().length > 0) {
        entries.push({ node, original: node.textContent })
      }
      node = walker.nextNode()
    }
    return entries
  }, [])

  const startSimulation = useCallback(
    (element: HTMLElement) => {
      targetRef.current = element
      const entries = captureTextNodes(element)

      // Shuffle every 300ms for a disorienting reading experience
      intervalRef.current = setInterval(() => {
        shuffleEntries(entries)
      }, 300)

      // Initial shuffle
      shuffleEntries(entries)
    },
    [captureTextNodes],
  )

  const stopSimulation = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    // Restore is handled by re-capturing if needed; the entries
    // are local to startSimulation, so we re-read from DOM.
    targetRef.current = null
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Auto-start/stop based on active flag, using a stable ref for entries
  useEffect(() => {
    if (!active || !targetRef.current) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    const entries = captureTextNodes(targetRef.current)
    shuffleEntries(entries)
    intervalRef.current = setInterval(() => {
      shuffleEntries(entries)
    }, 300)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      // Restore original text on cleanup
      restoreEntries(entries)
    }
  }, [active, captureTextNodes])

  return { startSimulation, stopSimulation, targetRef }
}

/* --- Internal types and helpers --- */

interface TextNodeEntry {
  node: Node
  original: string
}

/** Shuffle the text content of captured text nodes. */
function shuffleEntries(entries: TextNodeEntry[]): void {
  for (const entry of entries) {
    if (entry.node.parentNode) {
      entry.node.textContent = shuffleWords(entry.original)
    }
  }
}

/** Restore original text content for captured text nodes. */
function restoreEntries(entries: TextNodeEntry[]): void {
  for (const entry of entries) {
    if (entry.node.parentNode) {
      entry.node.textContent = entry.original
    }
  }
}

/**
 * Shuffle the interior letters of each word in a string.
 * Preserves first and last characters. Words with 3 or fewer
 * characters are left unchanged.
 */
function shuffleWords(text: string): string {
  return text.replace(/\b([a-zA-ZÀ-ÿ])([a-zA-ZÀ-ÿ]{2,})([a-zA-ZÀ-ÿ])\b/g, (_match, first, middle, last) => {
    const chars = middle.split('')
    // Fisher-Yates shuffle on the interior
    for (let i = chars.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      const temp = chars[i]
      chars[i] = chars[j]
      chars[j] = temp
    }
    return first + chars.join('') + last
  })
}
