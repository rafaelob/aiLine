'use client'

import { useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { SetupConfig } from '../setup-types'

interface StepSecurityProps {
  config: SetupConfig
  onChange: (field: keyof SetupConfig, value: string) => void
  errors: Record<string, string>
}

/**
 * Security & Media step: JWT secret, CORS origins, optional ElevenLabs key.
 */
export function StepSecurity({ config, onChange, errors }: StepSecurityProps) {
  const t = useTranslations('setup')

  const generateJwtSecret = useCallback(() => {
    const bytes = new Uint8Array(32)
    crypto.getRandomValues(bytes)
    const secret = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
    onChange('jwtSecret', secret)
  }, [onChange])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('security_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('security_desc')}</p>
      </div>

      {/* JWT Secret */}
      <div className="space-y-1.5">
        <label htmlFor="jwt-secret" className="block text-sm font-medium text-[var(--color-text)]">
          {t('jwt_secret')}
        </label>
        <div className="flex gap-2">
          <input
            id="jwt-secret"
            type="text"
            value={config.jwtSecret}
            onChange={(e) => onChange('jwtSecret', e.target.value)}
            placeholder={t('jwt_secret_placeholder')}
            autoComplete="off"
            className={cn(
              'flex-1 px-3 py-2.5 rounded-[var(--radius-sm)]',
              'border bg-[var(--color-surface)] text-[var(--color-text)]',
              'text-sm font-mono placeholder:text-[var(--color-muted)]/60',
              'input-focus-ring',
              errors.jwtSecret ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'
            )}
          />
          <button
            type="button"
            onClick={generateJwtSecret}
            className={cn(
              'px-4 py-2.5 rounded-[var(--radius-sm)] text-sm font-medium whitespace-nowrap',
              'border border-[var(--color-primary)] text-[var(--color-primary)]',
              'hover:bg-[var(--color-primary)]/5',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
              'transition-colors'
            )}
          >
            {t('jwt_generate')}
          </button>
        </div>
        {errors.jwtSecret && (
          <p className="text-xs text-[var(--color-error)]" role="alert">{errors.jwtSecret}</p>
        )}
      </div>

      {/* CORS Origins */}
      <div className="space-y-1.5">
        <label htmlFor="cors-origins" className="block text-sm font-medium text-[var(--color-text)]">
          {t('cors_origins')}
        </label>
        <input
          id="cors-origins"
          type="text"
          value={config.corsOrigins}
          onChange={(e) => onChange('corsOrigins', e.target.value)}
          placeholder={t('cors_placeholder')}
          autoComplete="off"
          className={cn(
            'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
            'border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]',
            'text-sm placeholder:text-[var(--color-muted)]/60',
            'input-focus-ring'
          )}
        />
        <p className="text-xs text-[var(--color-muted)]">{t('cors_help')}</p>
      </div>

      {/* ElevenLabs (optional) */}
      <div className="space-y-1.5">
        <label htmlFor="elevenlabs-key" className="block text-sm font-medium text-[var(--color-text)]">
          {t('elevenlabs_key')}
        </label>
        <input
          id="elevenlabs-key"
          type="password"
          value={config.elevenlabsKey}
          onChange={(e) => onChange('elevenlabsKey', e.target.value)}
          placeholder={t('elevenlabs_placeholder')}
          autoComplete="off"
          className={cn(
            'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
            'border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]',
            'text-sm placeholder:text-[var(--color-muted)]/60',
            'input-focus-ring'
          )}
        />
      </div>
    </div>
  )
}
