/** Shared API configuration for all client-side fetch calls. */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

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
  const devTeacherId = process.env.NEXT_PUBLIC_DEV_TEACHER_ID
  if (devTeacherId) {
    return { 'X-Teacher-ID': devTeacherId }
  }
  return {}
}
