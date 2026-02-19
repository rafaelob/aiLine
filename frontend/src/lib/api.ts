/** Shared API configuration for all client-side fetch calls. */

import { useAuthStore } from '../stores/auth-store'

export const API_BASE = '/api'

/**
 * Check if a JWT token has expired by decoding the payload.
 * Returns true if expired or unparseable (safe default).
 */
function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return true
    // Base64url decode the payload
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(atob(payload)) as { exp?: number }
    if (!decoded.exp) return true // No expiry claim — treat as expired for safety
    // Add 30s buffer to avoid edge-case rejections
    return decoded.exp < Date.now() / 1000 + 30
  } catch {
    return true // Unparseable token — treat as expired
  }
}

/** Session storage key for the active demo profile. */
const DEMO_PROFILE_KEY = 'ailine_demo_profile'

/** Valid demo profile keys — must match backend seed data. */
const VALID_DEMO_PROFILES = new Set([
  'teacher',
  'student-asd',
  'student-adhd',
  'student-dyslexia',
  'student-hearing',
  'parent',
])

/** Custom event dispatched when the demo profile changes. */
export const PROFILE_CHANGE_EVENT = 'ailine-profile-change'

/** Get the current demo profile key, or null if none is active. */
export function getCurrentProfile(): string | null {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem(DEMO_PROFILE_KEY) ?? null
}

/** Set the current demo profile and notify listeners. */
export function setDemoProfile(profileKey: string): void {
  sessionStorage.setItem(DEMO_PROFILE_KEY, profileKey)
  // Clear any existing JWT so the demo header takes precedence
  sessionStorage.removeItem('ailine_token')
  window.dispatchEvent(
    new CustomEvent(PROFILE_CHANGE_EVENT, { detail: profileKey }),
  )
}

/** Clear the active demo profile. */
export function clearDemoProfile(): void {
  sessionStorage.removeItem(DEMO_PROFILE_KEY)
  window.dispatchEvent(
    new CustomEvent(PROFILE_CHANGE_EVENT, { detail: null }),
  )
}

/** Build auth headers from available token sources.
 *
 * Priority:
 * 1. Persisted auth store JWT (from real login via zustand-persist)
 * 2. Session/localStorage JWT (legacy paths)
 * 3. Demo profile header
 * 4. Dev teacher ID fallback
 */
export function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {}

  // 1. Auth store token (in-memory Zustand state — NOT persisted to localStorage).
  // SECURITY: Token lives only in JS memory to mitigate XSS token theft.
  try {
    const { token, logout } = useAuthStore.getState()
    if (token && !isTokenExpired(token)) {
      return { Authorization: `Bearer ${token}` }
    }
    if (token && isTokenExpired(token)) {
      logout()
    }
  } catch {
    // Store not initialized — fall through
  }

  // 2. Legacy sessionStorage JWT (with expiry check)
  // SECURITY: localStorage fallback removed — XSS vector (Sprint 26)
  const token = sessionStorage.getItem('ailine_token')
  if (token && !isTokenExpired(token)) {
    return { Authorization: `Bearer ${token}` }
  }

  // 3. Active demo profile (validate against allowlist)
  const demoProfile = getCurrentProfile()
  if (demoProfile && VALID_DEMO_PROFILES.has(demoProfile)) {
    return { 'X-Teacher-ID': `demo-${demoProfile}` }
  }

  // 4. Dev teacher ID fallback
  const devTeacherId = process.env.NEXT_PUBLIC_DEV_TEACHER_ID
  if (devTeacherId) {
    return { 'X-Teacher-ID': devTeacherId }
  }

  return {}
}
