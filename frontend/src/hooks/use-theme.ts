'use client'

import { useCallback, useEffect } from 'react'
import { useSyncExternalStore } from 'react'
import type { PersonaId } from '@/types/accessibility'

const THEME_STORAGE_KEY = 'ailine-persona-theme'
const DEFAULT_PERSONA: PersonaId = 'standard'

/**
 * Map PersonaId (underscored TypeScript identifier) to the CSS
 * data-theme value (hyphenated, as defined in globals.css).
 * Only entries that differ from the PersonaId are listed.
 */
const PERSONA_TO_CSS_THEME: Partial<Record<PersonaId, string>> = {
  high_contrast: 'high-contrast',
  low_vision: 'low-vision',
  screen_reader: 'screen-reader',
}

/**
 * Resolve the CSS data-theme value for a given PersonaId or theme string.
 *
 * Exported so that other components can map underscored TypeScript
 * identifiers to hyphenated CSS data-theme values consistently.
 */
export function cssTheme(persona: string): string {
  return (PERSONA_TO_CSS_THEME as Record<string, string>)[persona] ?? persona
}

/**
 * Theme switching hook with localStorage persistence.
 * Applies data-theme attribute to document.body (ADR-019).
 * Uses useSyncExternalStore to read localStorage without setState-in-effect.
 */
export function useTheme() {
  const activePersona = useSyncExternalStore(
    subscribeToStorage,
    getPersonaSnapshot,
    getServerSnapshot,
  )

  // Apply theme to DOM on mount and when persona changes
  useEffect(() => {
    applyTheme(activePersona)
  }, [activePersona])

  const switchTheme = useCallback((persona: PersonaId) => {
    localStorage.setItem(THEME_STORAGE_KEY, persona)
    applyTheme(persona)
    // Notify other useSyncExternalStore subscribers
    window.dispatchEvent(new StorageEvent('storage', { key: THEME_STORAGE_KEY }))
  }, [])

  const resetTheme = useCallback(() => {
    switchTheme(DEFAULT_PERSONA)
  }, [switchTheme])

  return {
    activePersona,
    switchTheme,
    resetTheme,
  } as const
}

/** Apply theme directly to the DOM without React re-render (ADR-019). */
function applyTheme(persona: PersonaId): void {
  const theme = cssTheme(persona)
  document.body.setAttribute('data-theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
}

const VALID_PERSONAS = new Set<string>([
  'standard',
  'high_contrast',
  'tea',
  'tdah',
  'dyslexia',
  'low_vision',
  'hearing',
  'motor',
  'screen_reader',
])

function isValidPersona(value: string): boolean {
  return VALID_PERSONAS.has(value)
}

function getPersonaSnapshot(): PersonaId {
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  if (stored && isValidPersona(stored)) {
    return stored as PersonaId
  }
  return DEFAULT_PERSONA
}

function getServerSnapshot(): PersonaId {
  return DEFAULT_PERSONA
}

function subscribeToStorage(callback: () => void): () => void {
  const handler = (e: StorageEvent) => {
    if (e.key === THEME_STORAGE_KEY || e.key === null) {
      callback()
    }
  }
  window.addEventListener('storage', handler)
  return () => window.removeEventListener('storage', handler)
}
