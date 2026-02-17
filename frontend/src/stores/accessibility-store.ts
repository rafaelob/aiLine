import { create } from 'zustand'
import { cssTheme } from '@/hooks/use-theme'

/**
 * Accessibility preferences store.
 * Persists theme, font size, and motion preferences to localStorage.
 * Theme switching is done via DOM attribute, not React state (ADR-019).
 */

const STORAGE_KEY = 'ailine-a11y-prefs'

interface A11yPrefs {
  theme: string
  fontSize: string
  reducedMotion: boolean
  lowDistraction: boolean
  focusMode: boolean
  bionicReading: boolean
}

/** Check the OS-level prefers-reduced-motion media query. */
function getSystemReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function loadPrefs(): A11yPrefs {
  if (typeof window === 'undefined') {
    return { theme: 'standard', fontSize: 'medium', reducedMotion: false, lowDistraction: false, focusMode: false, bionicReading: false }
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<A11yPrefs>
      return {
        theme: parsed.theme ?? 'standard',
        fontSize: parsed.fontSize ?? 'medium',
        reducedMotion: parsed.reducedMotion ?? false,
        lowDistraction: parsed.lowDistraction ?? false,
        focusMode: parsed.focusMode ?? false,
        bionicReading: parsed.bionicReading ?? false,
      }
    }
  } catch {
    // Corrupted storage — fall back to defaults
  }
  // No stored preference: inherit reducedMotion from OS (FINDING-19)
  return {
    theme: 'standard',
    fontSize: 'medium',
    reducedMotion: getSystemReducedMotion(),
    lowDistraction: false,
    focusMode: false,
    bionicReading: false,
  }
}

function savePrefs(prefs: A11yPrefs) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
  } catch {
    // Storage full — fail silently
  }
}

export interface AccessibilityState extends A11yPrefs {
  setTheme: (theme: string) => void
  setFontSize: (fontSize: string) => void
  setReducedMotion: (reduced: boolean) => void
  setLowDistraction: (low: boolean) => void
  toggleFocusMode: () => void
  toggleBionicReading: () => void
  hydrate: () => void
}

export const useAccessibilityStore = create<AccessibilityState>((set, get) => ({
  theme: 'standard',
  fontSize: 'medium',
  reducedMotion: false,
  lowDistraction: false,
  focusMode: false,
  bionicReading: false,

  setTheme: (theme: string) => {
    set({ theme })
    savePrefs({ ...get(), theme })
  },

  setFontSize: (fontSize: string) => {
    set({ fontSize })
    savePrefs({ ...get(), fontSize })
  },

  setReducedMotion: (reduced: boolean) => {
    set({ reducedMotion: reduced })
    savePrefs({ ...get(), reducedMotion: reduced })
    if (typeof document !== 'undefined') {
      document.body.setAttribute('data-reduced-motion', String(reduced))
    }
  },

  setLowDistraction: (low: boolean) => {
    set({ lowDistraction: low })
    savePrefs({ ...get(), lowDistraction: low })
  },

  toggleFocusMode: () => {
    const next = !get().focusMode
    set({ focusMode: next })
    savePrefs({ ...get(), focusMode: next })
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('cognitive-curtain-active', next)
    }
  },

  toggleBionicReading: () => {
    const next = !get().bionicReading
    set({ bionicReading: next })
    savePrefs({ ...get(), bionicReading: next })
  },

  hydrate: () => {
    const prefs = loadPrefs()
    set(prefs)
    // Apply to DOM immediately — map underscored TypeScript IDs to hyphenated CSS values
    if (typeof document !== 'undefined') {
      const css = cssTheme(prefs.theme)
      document.body.setAttribute('data-theme', css)
      document.documentElement.setAttribute('data-theme', css)
      document.body.setAttribute('data-reduced-motion', String(prefs.reducedMotion))
      document.documentElement.style.setProperty(
        '--font-size-base',
        fontSizeMap[prefs.fontSize] ?? '16px'
      )
      document.body.classList.toggle('cognitive-curtain-active', prefs.focusMode)
    }
    // Listen for OS-level reduced motion changes (FINDING-19).
    // Only update if the user has NOT explicitly overridden via setReducedMotion.
    if (typeof window !== 'undefined') {
      const mql = window.matchMedia('(prefers-reduced-motion: reduce)')
      const handler = (e: MediaQueryListEvent) => {
        // Only sync with OS when no stored user preference exists
        const stored = localStorage.getItem(STORAGE_KEY)
        if (!stored) {
          set({ reducedMotion: e.matches })
        }
      }
      mql.addEventListener('change', handler)
      // Store cleanup function for testing
      ;(useAccessibilityStore as unknown as Record<string, unknown>)
        ._mqCleanup = () => mql.removeEventListener('change', handler)
    }
  },
}))

const fontSizeMap: Record<string, string> = {
  small: '14px',
  medium: '16px',
  large: '20px',
  xlarge: '24px',
}
