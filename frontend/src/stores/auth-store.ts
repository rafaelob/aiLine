'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole =
  | 'super_admin'
  | 'school_admin'
  | 'teacher'
  | 'student'
  | 'parent'

export interface AuthUser {
  id: string
  email: string
  display_name: string
  role: UserRole
  org_id?: string
  locale: string
  avatar_url: string
  accessibility_profile: string
  is_active: boolean
}

interface AuthState {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: AuthUser) => void
  logout: () => void
  updateUser: (updates: Partial<AuthUser>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token, user) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: 'ailine-auth',
      // SECURITY: Do NOT persist JWT token to localStorage (XSS risk).
      // Only persist user profile for display; token lives in memory only.
      // isAuthenticated is NOT persisted — it requires an active token.
      // On reload, user profile is available but isAuthenticated = false
      // until a fresh login provides a new token.
      partialize: (state) => ({
        user: state.user,
      }),
      // Clear zombie state: if token is absent on rehydrate but user
      // profile was persisted, wipe the stale user to avoid confusion.
      onRehydrateStorage: () => (state) => {
        if (state && !state.token && state.user) {
          state.user = null
          state.isAuthenticated = false
        }
      },
    },
  ),
)
