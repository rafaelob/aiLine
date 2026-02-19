'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { SetupConfig } from '../setup-types'

interface StepInfrastructureProps {
  config: SetupConfig
  onChange: (field: keyof SetupConfig, value: string) => void
  errors: Record<string, string>
}

/**
 * Infrastructure step: database URL, Redis URL, and port configuration.
 * Pre-filled with Docker Compose defaults.
 */
export function StepInfrastructure({ config, onChange, errors }: StepInfrastructureProps) {
  const t = useTranslations('setup')

  const fields: {
    id: keyof SetupConfig
    label: string
    placeholder: string
    type?: string
  }[] = [
    { id: 'databaseUrl', label: t('db_url'), placeholder: t('db_url_placeholder') },
    { id: 'redisUrl', label: t('redis_url'), placeholder: t('redis_url_placeholder') },
    { id: 'apiPort', label: t('api_port'), placeholder: '8011', type: 'number' },
    { id: 'frontendPort', label: t('frontend_port'), placeholder: '3000', type: 'number' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('infra_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('infra_desc')}</p>
      </div>

      <div className="space-y-4">
        {fields.map((field) => (
          <div key={field.id} className="space-y-1.5">
            <label htmlFor={`infra-${field.id}`} className="block text-sm font-medium text-[var(--color-text)]">
              {field.label}
            </label>
            <input
              id={`infra-${field.id}`}
              type={field.type ?? 'text'}
              value={config[field.id] as string}
              onChange={(e) => onChange(field.id, e.target.value)}
              placeholder={field.placeholder}
              autoComplete="off"
              className={cn(
                'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
                'border bg-[var(--color-surface)] text-[var(--color-text)]',
                'text-sm placeholder:text-[var(--color-muted)]/60',
                'input-focus-ring',
                errors[field.id] ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'
              )}
            />
            {errors[field.id] && (
              <p className="text-xs text-[var(--color-error)]" role="alert">{errors[field.id]}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
