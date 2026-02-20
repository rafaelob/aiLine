import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  API_BASE,
  getCurrentProfile,
  setDemoProfile,
  clearDemoProfile,
  getAuthHeaders,
  PROFILE_CHANGE_EVENT,
} from './api'
import { useAuthStore } from '../stores/auth-store'

/** Create a minimal valid JWT with a given exp timestamp. */
function makeJwt(exp: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ sub: 'user-1', exp }))
  return `${header}.${payload}.signature`
}

describe('api module', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
    vi.unstubAllEnvs()
  })

  describe('API_BASE', () => {
    it('is /api', () => {
      expect(API_BASE).toBe('/api')
    })
  })

  describe('getCurrentProfile', () => {
    it('returns null when no profile is set', () => {
      expect(getCurrentProfile()).toBeNull()
    })

    it('returns the stored profile key', () => {
      sessionStorage.setItem('ailine_demo_profile', 'teacher')
      expect(getCurrentProfile()).toBe('teacher')
    })
  })

  describe('setDemoProfile', () => {
    it('stores the profile key in sessionStorage', () => {
      setDemoProfile('student-asd')
      expect(sessionStorage.getItem('ailine_demo_profile')).toBe('student-asd')
    })

    it('clears any existing JWT from sessionStorage', () => {
      sessionStorage.setItem('ailine_token', 'old-jwt')
      setDemoProfile('teacher')
      expect(sessionStorage.getItem('ailine_token')).toBeNull()
    })

    it('dispatches a custom event with the profile key', () => {
      const listener = vi.fn()
      window.addEventListener(PROFILE_CHANGE_EVENT, listener)

      setDemoProfile('parent')

      expect(listener).toHaveBeenCalledTimes(1)
      const event = listener.mock.calls[0][0] as CustomEvent
      expect(event.detail).toBe('parent')

      window.removeEventListener(PROFILE_CHANGE_EVENT, listener)
    })
  })

  describe('clearDemoProfile', () => {
    it('removes the profile from sessionStorage', () => {
      sessionStorage.setItem('ailine_demo_profile', 'teacher')
      clearDemoProfile()
      expect(sessionStorage.getItem('ailine_demo_profile')).toBeNull()
    })

    it('dispatches a custom event with null detail', () => {
      const listener = vi.fn()
      window.addEventListener(PROFILE_CHANGE_EVENT, listener)

      clearDemoProfile()

      const event = listener.mock.calls[0][0] as CustomEvent
      expect(event.detail).toBeNull()

      window.removeEventListener(PROFILE_CHANGE_EVENT, listener)
    })
  })

  describe('getAuthHeaders', () => {
    it('returns Bearer token from auth store when valid', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const token = makeJwt(futureExp)
      useAuthStore.setState({ token, isAuthenticated: true })

      const headers = getAuthHeaders()
      expect(headers).toEqual({ Authorization: `Bearer ${token}` })
    })

    it('calls logout when auth store token is expired', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600
      const token = makeJwt(pastExp)
      useAuthStore.setState({ token, isAuthenticated: true, user: { id: 'u1' } as never })

      getAuthHeaders()

      const state = useAuthStore.getState()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })

    it('falls back to sessionStorage JWT when store has no token', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const token = makeJwt(futureExp)
      sessionStorage.setItem('ailine_token', token)

      const headers = getAuthHeaders()
      expect(headers).toEqual({ Authorization: `Bearer ${token}` })
    })

    it('falls back to demo profile header when no JWT available (short key)', () => {
      sessionStorage.setItem('ailine_demo_profile', 'teacher')

      const headers = getAuthHeaders()
      expect(headers).toEqual({ 'X-Teacher-ID': 'demo-teacher' })
    })

    it('falls back to demo profile header for landing page long key', () => {
      sessionStorage.setItem('ailine_demo_profile', 'teacher-ms-johnson')

      const headers = getAuthHeaders()
      expect(headers).toEqual({ 'X-Teacher-ID': 'demo-teacher-ms-johnson' })
    })

    it('rejects invalid demo profile keys', () => {
      sessionStorage.setItem('ailine_demo_profile', 'hacker-evil')

      const headers = getAuthHeaders()
      // Invalid profile should not produce X-Teacher-ID
      expect(headers['X-Teacher-ID']).toBeUndefined()
    })

    it('accepts all valid demo profile keys (short and long formats)', () => {
      const validProfiles = [
        // Short format (login page)
        'teacher', 'student-asd', 'student-adhd', 'student-dyslexia',
        'student-hearing', 'parent',
        // Long format (landing page — matches backend demo_profiles.py)
        'teacher-ms-johnson', 'student-alex-tea', 'student-maya-adhd',
        'student-lucas-dyslexia', 'student-sofia-hearing', 'parent-david',
        // Admin profiles (same in both flows)
        'admin-principal', 'admin-super',
      ]
      for (const profile of validProfiles) {
        sessionStorage.setItem('ailine_demo_profile', profile)
        const headers = getAuthHeaders()
        expect(headers).toEqual({ 'X-Teacher-ID': `demo-${profile}` })
      }
    })

    it('falls back to dev teacher ID from environment', () => {
      vi.stubEnv('NEXT_PUBLIC_DEV_TEACHER_ID', 'dev-teacher-001')

      const headers = getAuthHeaders()
      expect(headers).toEqual({ 'X-Teacher-ID': 'dev-teacher-001' })
    })

    it('returns empty headers when nothing is available', () => {
      const headers = getAuthHeaders()
      expect(headers).toEqual({})
    })

    it('auth store JWT takes priority over demo profile', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const token = makeJwt(futureExp)
      useAuthStore.setState({ token, isAuthenticated: true })
      sessionStorage.setItem('ailine_demo_profile', 'teacher')

      const headers = getAuthHeaders()
      expect(headers).toEqual({ Authorization: `Bearer ${token}` })
    })

    it('sessionStorage JWT takes priority over demo profile', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const token = makeJwt(futureExp)
      sessionStorage.setItem('ailine_token', token)
      sessionStorage.setItem('ailine_demo_profile', 'teacher')

      const headers = getAuthHeaders()
      expect(headers).toEqual({ Authorization: `Bearer ${token}` })
    })

    it('handles malformed JWT gracefully (treats as expired)', () => {
      useAuthStore.setState({ token: 'not-a-jwt', isAuthenticated: true })

      // Should not throw
      const headers = getAuthHeaders()
      // Malformed token treated as expired, falls through
      expect(headers.Authorization).toBeUndefined()
    })

    it('handles JWT without exp claim (treats as expired)', () => {
      const header = btoa(JSON.stringify({ alg: 'HS256' }))
      const payload = btoa(JSON.stringify({ sub: 'user-1' }))
      const token = `${header}.${payload}.sig`
      useAuthStore.setState({ token, isAuthenticated: true })

      const headers = getAuthHeaders()
      expect(headers.Authorization).toBeUndefined()
    })
  })
})
