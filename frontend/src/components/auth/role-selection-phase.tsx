'use client'

import { motion } from 'motion/react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { cn } from '@/lib/cn'
import type { UserRole } from '@/stores/auth-store'
import { ROLES } from './login-data'
import { RoleIcon } from './role-icon'

interface RoleSelectionPhaseProps {
  locale: string
  noMotion: boolean
  onRoleSelect: (role: UserRole) => void
}

/**
 * Phase 1 of the login page: role selection grid.
 * Renders ROLES as a radiogroup of cards.
 */
export function RoleSelectionPhase({ locale, noMotion, onRoleSelect }: RoleSelectionPhaseProps) {
  const t = useTranslations('login')

  return (
    <motion.div
      key="role-selection"
      initial={noMotion ? undefined : { opacity: 0, y: 16 }}
      animate={noMotion ? undefined : { opacity: 1, y: 0 }}
      exit={noMotion ? undefined : { opacity: 0, y: -16 }}
      transition={noMotion ? undefined : { duration: 0.3 }}
    >
      <h2 className="text-center text-lg font-semibold text-[var(--color-text)] mb-6">
        {t('choose_role')}
      </h2>

      <div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        role="group"
        aria-label={t('choose_role')}
      >
        {ROLES.map((role, i) => (
          <motion.button
            key={role.id}
            type="button"
            initial={noMotion ? undefined : { opacity: 0, y: 20 }}
            animate={noMotion ? undefined : { opacity: 1, y: 0 }}
            transition={
              noMotion ? undefined : { delay: i * 0.06, duration: 0.35 }
            }
            onClick={() => onRoleSelect(role.id)}
            className={cn(
              'group relative overflow-hidden rounded-2xl p-5',
              'glass card-hover gradient-border-glass',
              'flex flex-col items-center gap-3 text-center',
              'cursor-pointer',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2',
            )}
            aria-label={t(`role_${role.id}`)}
          >
            {role.badge && (
              <div
                className={cn(
                  'absolute -top-px -right-px px-3 py-1',
                  'rounded-bl-xl rounded-tr-2xl',
                  'text-[10px] font-bold uppercase tracking-widest',
                  'bg-gradient-to-r text-white',
                  role.color,
                  'shadow-sm',
                )}
              >
                {t(role.badge)}
              </div>
            )}

            {/* Hover gradient overlay */}
            <div
              className={cn(
                'absolute inset-0 opacity-0 transition-opacity duration-300',
                'group-hover:opacity-100 pointer-events-none',
              )}
              style={{
                background:
                  'radial-gradient(ellipse at 50% 0%, color-mix(in srgb, var(--color-primary) 6%, transparent) 0%, transparent 70%)',
              }}
              aria-hidden="true"
            />

            <div
              className={cn(
                'relative flex items-center justify-center w-14 h-14',
                'rounded-xl bg-gradient-to-br text-white',
                role.color,
              )}
            >
              <RoleIcon path={role.icon} />
            </div>

            <div className="relative">
              <h3 className="text-sm font-semibold text-[var(--color-text)]">
                {t(`role_${role.id}`)}
              </h3>
              <p className="mt-1 text-xs text-[var(--color-muted)] leading-relaxed">
                {t(`role_${role.id}_desc`)}
              </p>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Back to landing link */}
      <div className="mt-8 text-center">
        <Link
          // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed path
          href={`/${locale}` as any}
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
