'use client'

import { useState, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useAuthStore, type UserRole } from '@/stores/auth-store'
import { API_BASE, setDemoProfile, getAuthHeaders } from '@/lib/api'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { cssTheme } from '@/hooks/use-theme'
import { DEMO_PROFILES_BY_ROLE, type DemoProfile } from '@/components/auth/login-data'
import { RoleSelectionPhase } from '@/components/auth/role-selection-phase'
import { LoginFormPhase } from '@/components/auth/login-form-phase'

/* ------------------------------------------------------------------ */
/*  Login Page (orchestrator)                                          */
/* ------------------------------------------------------------------ */

export default function LoginPage() {
  const router = useRouter()
  const params = useParams()
  const locale = (params?.locale as string) ?? 'en'
  const t = useTranslations('login')
  const login = useAuthStore((s) => s.login)
  const setTheme = useAccessibilityStore((s) => s.setTheme)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRoleSelect = useCallback((role: UserRole) => {
    setSelectedRole(role)
    setError(null)
  }, [])

  const handleBack = useCallback(() => {
    setSelectedRole(null)
    setError(null)
    setEmail('')
    setPassword('')
  }, [])

  const handleDemoLogin = useCallback(
    (profile: DemoProfile) => {
      setDemoProfile(profile.key)

      if (profile.accessibility) {
        const css = cssTheme(profile.accessibility)
        setTheme(profile.accessibility)
        if (typeof document !== 'undefined') {
          document.body.setAttribute('data-theme', css)
          document.documentElement.setAttribute('data-theme', css)
        }
      }

      router.push(`/${locale}${profile.route}`)
    },
    [locale, router, setTheme],
  )

  const handleEmailLogin = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (!selectedRole || !email || !password) return

      setIsLoading(true)
      setError(null)

      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
          },
          body: JSON.stringify({ email, password, role: selectedRole }),
        })

        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(
            (body as { detail?: string }).detail ?? t('error_credentials'),
          )
        }

        const data = (await res.json()) as {
          access_token: string
          user: {
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
        }

        login(data.access_token, data.user)
        router.push(`/${locale}/dashboard`)
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('error_generic'),
        )
      } finally {
        setIsLoading(false)
      }
    },
    [selectedRole, email, password, locale, router, login, t],
  )

  const demoProfiles = selectedRole
    ? DEMO_PROFILES_BY_ROLE[selectedRole]
    : []

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background mesh gradient */}
      <div
        className="absolute inset-0 mesh-gradient-hero hero-noise -z-10"
        style={{ backgroundColor: 'var(--color-primary)', opacity: 0.06 }}
        aria-hidden="true"
      />

      {/* Decorative shapes */}
      <div
        className="absolute -top-32 -right-32 w-96 h-96 rounded-full opacity-5 animate-float-slow"
        style={{ background: 'var(--gradient-hero)' }}
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full opacity-5 animate-float-medium"
        style={{ background: 'var(--gradient-hero)' }}
        aria-hidden="true"
      />

      {/* Logo and title */}
      <motion.div
        initial={noMotion ? undefined : { opacity: 0, y: -16 }}
        animate={noMotion ? undefined : { opacity: 1, y: 0 }}
        transition={noMotion ? undefined : { duration: 0.5 }}
        className="text-center mb-10"
      >
        <div
          className={cn(
            'mx-auto mb-4 w-16 h-16 rounded-2xl flex items-center justify-center',
            'text-white font-bold text-2xl',
          )}
          style={{
            background: 'var(--gradient-hero)',
            boxShadow: 'var(--shadow-lg)',
          }}
          aria-hidden="true"
        >
          A
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text-animated">
          {t('title')}
        </h1>
        <p className="mt-2 text-sm text-[var(--color-muted)] max-w-md mx-auto">
          {t('subtitle')}
        </p>
      </motion.div>

      {/* Content area */}
      <div className="w-full max-w-3xl">
        <AnimatePresence mode="wait">
          {!selectedRole ? (
            <RoleSelectionPhase
              locale={locale}
              noMotion={noMotion}
              onRoleSelect={handleRoleSelect}
            />
          ) : (
            <LoginFormPhase
              locale={locale}
              noMotion={noMotion}
              selectedRole={selectedRole}
              demoProfiles={demoProfiles}
              email={email}
              password={password}
              isLoading={isLoading}
              error={error}
              onBack={handleBack}
              onDemoLogin={handleDemoLogin}
              onEmailChange={setEmail}
              onPasswordChange={setPassword}
              onSubmit={handleEmailLogin}
            />
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}
