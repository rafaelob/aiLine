'use client'

import { useRef, useEffect } from 'react'
import { motion } from 'motion/react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { cn } from '@/lib/cn'
import { localePath } from '@/lib/locale-path'
import type { UserRole } from '@/stores/auth-store'
import { ROLES, type DemoProfile } from './login-data'

interface LoginFormPhaseProps {
  locale: string
  noMotion: boolean
  selectedRole: UserRole
  demoProfiles: DemoProfile[]
  email: string
  password: string
  isLoading: boolean
  error: string | null
  onBack: () => void
  onDemoLogin: (profile: DemoProfile) => void
  onEmailChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
}

/**
 * Phase 2 of the login page: demo profiles + email/password form.
 * Shown after a role is selected.
 */
export function LoginFormPhase({
  locale,
  noMotion,
  selectedRole,
  demoProfiles,
  email,
  password,
  isLoading,
  error,
  onBack,
  onDemoLogin,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}: LoginFormPhaseProps) {
  const t = useTranslations('login')
  const tLanding = useTranslations('landing')
  const backButtonRef = useRef<HTMLButtonElement>(null)

  // Focus the back button when entering phase 2
  useEffect(() => {
    backButtonRef.current?.focus()
  }, [])

  return (
    <motion.div
      key="login-form"
      initial={noMotion ? undefined : { opacity: 0, y: 16 }}
      animate={noMotion ? undefined : { opacity: 1, y: 0 }}
      exit={noMotion ? undefined : { opacity: 0, y: -16 }}
      transition={noMotion ? undefined : { duration: 0.3 }}
    >
      {/* Back button */}
      <button
        ref={backButtonRef}
        type="button"
        onClick={onBack}
        className={cn(
          'mb-6 inline-flex items-center gap-2 text-sm',
          'text-[var(--color-muted)] hover:text-[var(--color-text)]',
          'transition-colors duration-200',
          'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] rounded-lg px-2 py-1',
        )}
        aria-label={t('back_to_roles')}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        {t('back_to_roles')}
      </button>

      <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">
        {t(`role_${selectedRole}`)}
      </h2>
      <p className="text-sm text-[var(--color-muted)] mb-6">
        {t(`role_${selectedRole}_desc`)}
      </p>

      {/* Demo profiles */}
      {demoProfiles.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-medium text-[var(--color-text)] mb-3 flex items-center gap-2">
            <span
              className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 text-white text-[10px] font-bold"
              aria-hidden="true"
            >
              D
            </span>
            {t('demo_section_title')}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {demoProfiles.map((profile, i) => (
              <motion.button
                key={profile.key}
                type="button"
                initial={noMotion ? undefined : { opacity: 0, y: 12 }}
                animate={noMotion ? undefined : { opacity: 1, y: 0 }}
                transition={
                  noMotion ? undefined : { delay: i * 0.06, duration: 0.3 }
                }
                onClick={() => onDemoLogin(profile)}
                className={cn(
                  'group relative overflow-hidden rounded-xl p-4',
                  'glass card-hover',
                  'flex items-start gap-3 text-left',
                  'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2',
                )}
                aria-label={`${tLanding('demo_enter_as')} ${profile.name}`}
              >
                <div
                  className={cn(
                    'flex items-center justify-center w-10 h-10',
                    'rounded-lg bg-gradient-to-br text-white',
                    'font-bold text-xs shrink-0',
                    profile.color,
                  )}
                  aria-hidden="true"
                >
                  {profile.avatar}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-[var(--color-text)] truncate">
                      {profile.name}
                    </span>
                    {profile.badge && (
                      <span
                        className={cn(
                          'inline-flex px-2 py-0.5 rounded-full',
                          'text-[10px] font-bold uppercase tracking-wider',
                          'bg-gradient-to-r text-white',
                          profile.color,
                        )}
                      >
                        {profile.badge}
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-[var(--color-muted)] leading-relaxed line-clamp-2">
                    {tLanding(profile.description)}
                  </p>
                </div>
                <div
                  className={cn(
                    'self-center shrink-0 text-[var(--color-muted)]',
                    'group-hover:text-[var(--color-primary)]',
                    'transition-colors duration-200',
                  )}
                  aria-hidden="true"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      )}

      {/* Divider */}
      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[var(--color-border)]" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-3 text-xs text-[var(--color-muted)] bg-[var(--color-bg)]">
            {t('or_sign_in')}
          </span>
        </div>
      </div>

      {/* Email/password form */}
      <form
        onSubmit={onSubmit}
        className="glass rounded-2xl p-6 space-y-4"
      >
        <div>
          <label
            htmlFor="login-email"
            className="block text-sm font-medium text-[var(--color-text)] mb-1.5"
          >
            {t('email_label')}
          </label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            placeholder={t('email_placeholder')}
            className={cn(
              'w-full px-4 py-3 rounded-xl',
              'bg-[var(--color-surface)] border border-[var(--color-border)]',
              'text-sm text-[var(--color-text)]',
              'placeholder:text-[var(--color-muted)]',
              'input-focus-ring',
              'transition-colors duration-200',
            )}
          />
        </div>

        <div>
          <label
            htmlFor="login-password"
            className="block text-sm font-medium text-[var(--color-text)] mb-1.5"
          >
            {t('password_label')}
          </label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder={t('password_placeholder')}
            className={cn(
              'w-full px-4 py-3 rounded-xl',
              'bg-[var(--color-surface)] border border-[var(--color-border)]',
              'text-sm text-[var(--color-text)]',
              'placeholder:text-[var(--color-muted)]',
              'input-focus-ring',
              'transition-colors duration-200',
            )}
          />
        </div>

        {error && (
          <div
            role="alert"
            className="px-4 py-3 rounded-xl bg-[color-mix(in_srgb,var(--color-error)_10%,transparent)] border border-[var(--color-error)]/20 text-sm text-[var(--color-error)]"
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading || !email || !password}
          className={cn(
            'w-full px-6 py-3 rounded-xl',
            'text-sm font-semibold text-white',
            'bg-gradient-to-r',
            ROLES.find((r) => r.id === selectedRole)?.color ??
              'from-blue-500 to-indigo-600',
            'shadow-md hover:shadow-lg hover:scale-[1.01]',
            'transition-all duration-200',
            'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2',
            'disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100',
            'btn-shimmer btn-press',
          )}
        >
          {isLoading ? (
            <span className="inline-flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  className="opacity-25"
                />
                <path
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  className="opacity-75"
                />
              </svg>
              {t('signing_in')}
            </span>
          ) : (
            t('sign_in')
          )}
        </button>
      </form>

      {/* Back to landing link */}
      <div className="mt-6 text-center">
        <Link
          href={localePath(locale, '/') as Parameters<typeof Link>[0]['href']}
          className={cn(
            'text-sm text-[var(--color-muted)] hover:text-[var(--color-primary)]',
            'transition-colors duration-200 underline-offset-4 hover:underline',
          )}
        >
          {t('back_to_home')}
        </Link>
      </div>
    </motion.div>
  )
}
