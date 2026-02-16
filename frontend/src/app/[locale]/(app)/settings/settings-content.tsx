'use client'

import { useTranslations, useLocale } from 'next-intl'
import Link from 'next/link'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { PrivacyPanel } from '@/components/privacy/privacy-panel'

const modelDisplay =
  process.env.NEXT_PUBLIC_DEFAULT_MODEL ?? 'Auto-routed (SmartRouter)'

export function SettingsContent() {
  const t = useTranslations('settings')
  const locale = useLocale()

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-4"
    >
      {/* AI Model */}
      <motion.section
        variants={itemVariants}
        className="glass card-hover rounded-2xl p-6"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
            style={{
              background:
                'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
            }}
            aria-hidden="true"
          >
            <ModelIcon />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-sm text-[var(--color-text)]">
              {t('ai_model')}
            </h2>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {t('ai_model_desc')}
            </p>
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)]">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)]" />
              <span className="text-xs font-medium text-[var(--color-text)]">
                {modelDisplay === 'Auto-routed (SmartRouter)'
                  ? t('auto_routed')
                  : modelDisplay}
              </span>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Language */}
      <motion.section
        variants={itemVariants}
        className="glass card-hover rounded-2xl p-6"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
            style={{
              background:
                'linear-gradient(135deg, var(--color-secondary), var(--color-primary))',
            }}
            aria-hidden="true"
          >
            <LanguageIcon />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-sm text-[var(--color-text)]">
              {t('language')}
            </h2>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {t('language_desc')}
            </p>
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)]">
              <span className="text-xs font-medium text-[var(--color-text)]">
                {t('current_language', { locale: locale.toUpperCase() })}
              </span>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Accessibility */}
      <motion.section
        variants={itemVariants}
        className="glass card-hover rounded-2xl p-6"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
            style={{
              background:
                'linear-gradient(135deg, #10b981, var(--color-primary))',
            }}
            aria-hidden="true"
          >
            <AccessibilityIcon />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-sm text-[var(--color-text)]">
              {t('accessibility_settings')}
            </h2>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {t('accessibility_desc')}
            </p>
            <Link
              href={`/${locale}/accessibility`}
              className={cn(
                'mt-3 inline-flex items-center gap-2 px-4 py-2',
                'rounded-xl text-xs font-semibold',
                'bg-[var(--color-surface-elevated)] border border-[var(--color-border)]',
                'text-[var(--color-text)]',
                'hover:bg-[var(--color-primary)]/10 hover:border-[var(--color-primary)]/30',
                'transition-all duration-200',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]'
              )}
            >
              {t('open_preferences')}
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Privacy & Data */}
      <motion.section
        variants={itemVariants}
        className="glass card-hover rounded-2xl p-6"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
            style={{
              background:
                'linear-gradient(135deg, #8b5cf6, var(--color-primary))',
            }}
            aria-hidden="true"
          >
            <ShieldIcon />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-sm text-[var(--color-text)]">
              {t('privacy')}
            </h2>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {t('privacy_desc')}
            </p>
            <div className="mt-3">
              <PrivacyPanel />
            </div>
          </div>
        </div>
      </motion.section>

      {/* About */}
      <motion.section
        variants={itemVariants}
        className="glass card-hover rounded-2xl p-6"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
            style={{
              background:
                'linear-gradient(135deg, #CC785C, #D4A574)',
            }}
            aria-hidden="true"
          >
            <InfoIcon />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-sm text-[var(--color-text)]">
              {t('about')}
            </h2>
            <div className="mt-2 space-y-1">
              <p className="text-xs text-[var(--color-muted)]">
                {t('version')}: v0.2.0
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {t('built_with')}
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {t('hackathon')}
              </p>
            </div>
          </div>
        </div>
      </motion.section>
    </motion.div>
  )
}

/* ===== Icon Components ===== */

function ModelIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  )
}

function LanguageIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  )
}

function AccessibilityIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="4" r="2" />
      <path d="M4 10h16" />
      <path d="M12 10v8" />
      <path d="M8 22l4-4 4 4" />
    </svg>
  )
}

function ShieldIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  )
}

function InfoIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  )
}
