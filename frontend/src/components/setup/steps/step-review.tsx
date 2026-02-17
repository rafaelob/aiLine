'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { SetupConfig } from '../setup-types'
import { LLM_PROVIDERS, EMBEDDING_OPTIONS, AGENT_MODELS } from '../setup-types'

interface StepReviewProps {
  config: SetupConfig
  applying: boolean
  applyStatus: 'idle' | 'writing' | 'done' | 'error'
  onApply: () => void
}

/** Mask a sensitive string, showing only the last 4 characters. */
function maskSecret(value: string): string {
  if (!value || value.length <= 4) return value ? '****' : ''
  return '****' + value.slice(-4)
}

/**
 * Review & Apply step: summary of all configuration with Apply button.
 */
export function StepReview({ config, applying, applyStatus, onApply }: StepReviewProps) {
  const t = useTranslations('setup')

  const providerLabel = LLM_PROVIDERS.find((p) => p.id === config.llmProvider)?.nameKey
  const embeddingLabel = EMBEDDING_OPTIONS.find((e) => e.id === config.embeddingProvider)?.name

  const sections = [
    {
      category: t('category_llm'),
      rows: [
        { label: t('ai_title'), value: providerLabel ? t(providerLabel) : '-' },
        { label: t('api_key'), value: maskSecret(config.llmApiKey) },
      ],
    },
    {
      category: t('category_embedding'),
      rows: [
        { label: t('embed_provider'), value: embeddingLabel ?? '-' },
        { label: t('embed_model'), value: config.embeddingModel },
        { label: t('embed_dimensions'), value: String(config.embeddingDimensions) },
      ],
    },
    {
      category: t('category_models'),
      rows: AGENT_MODELS.map((a) => ({
        label: t(a.nameKey),
        value: config[a.id] as string,
      })),
    },
    {
      category: t('category_infra'),
      rows: [
        { label: t('db_url'), value: config.databaseUrl },
        { label: t('redis_url'), value: config.redisUrl },
        { label: t('api_port'), value: config.apiPort },
        { label: t('frontend_port'), value: config.frontendPort },
      ],
    },
    {
      category: t('category_security'),
      rows: [
        { label: t('jwt_secret'), value: maskSecret(config.jwtSecret) },
        { label: t('cors_origins'), value: config.corsOrigins },
        { label: t('elevenlabs_key'), value: config.elevenlabsKey ? maskSecret(config.elevenlabsKey) : '-' },
      ],
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('review_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('review_desc')}</p>
      </div>

      {/* Configuration summary table */}
      <div className="space-y-4">
        {sections.map((section) => (
          <div
            key={section.category}
            className={cn(
              'rounded-[var(--radius-md)] border border-[var(--color-border)]',
              'overflow-hidden'
            )}
          >
            <div className="px-4 py-2.5 bg-[var(--color-surface-elevated)] border-b border-[var(--color-border)]">
              <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                {section.category}
              </h3>
            </div>
            <div className="divide-y divide-[var(--color-border)]">
              {section.rows.map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between px-4 py-3 bg-[var(--color-surface)]"
                >
                  <span className="text-sm text-[var(--color-muted)]">{row.label}</span>
                  <span className="text-sm font-mono text-[var(--color-text)] text-right max-w-[60%] truncate">
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Apply button and status */}
      {applyStatus === 'done' ? (
        <div
          className={cn(
            'p-4 rounded-[var(--radius-md)]',
            'bg-[var(--color-success)]/10 border border-[var(--color-success)]/30'
          )}
          role="status"
        >
          <div className="flex items-center gap-2 mb-2">
            <svg className="text-[var(--color-success)]" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span className="text-sm font-semibold text-[var(--color-success)]">
              {t('config_saved')}
            </span>
          </div>
          <p className="text-sm text-[var(--color-text)] mb-2">
            {t('restart_hint')}
          </p>
          <code className="block text-xs font-mono bg-[var(--color-surface-elevated)] text-[var(--color-text)] px-3 py-2 rounded-[var(--radius-sm)]">
            {t('restart_command')}
          </code>
        </div>
      ) : (
        <button
          type="button"
          onClick={onApply}
          disabled={applying}
          className={cn(
            'w-full px-6 py-3 rounded-[var(--radius-md)]',
            'text-sm font-semibold',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'hover:bg-[var(--color-primary-hover)]',
            'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors',
            'btn-press'
          )}
        >
          {applying ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              {applyStatus === 'writing' ? t('writing_config') : t('applying')}
            </span>
          ) : (
            t('apply')
          )}
        </button>
      )}

      {applyStatus === 'error' && (
        <p className="text-xs text-[var(--color-error)] text-center" role="alert">
          {t('key_invalid')}
        </p>
      )}
    </div>
  )
}
