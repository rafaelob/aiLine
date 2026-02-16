/** Shared API configuration for all client-side fetch calls. */

export const API_BASE = '/api'

/** Session storage key for the active demo profile. */
const DEMO_PROFILE_KEY = 'ailine_demo_profile'

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

/** Build auth headers from available token sources. */
export function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== 'undefined'
      ? sessionStorage.getItem('ailine_token') ??
        localStorage.getItem('ailine_token')
      : null
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  // Check for active demo profile
  const demoProfile = getCurrentProfile()
  if (demoProfile) {
    return { 'X-Teacher-ID': `demo-${demoProfile}` }
  }
  const devTeacherId = process.env.NEXT_PUBLIC_DEV_TEACHER_ID
  if (devTeacherId) {
    return { 'X-Teacher-ID': devTeacherId }
  }
  return {}
}
