'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { EmbeddingProvider } from '../setup-types'
import { EMBEDDING_OPTIONS } from '../setup-types'

interface StepEmbeddingsProps {
  provider: EmbeddingProvider
  model: string
  dimensions: number
  onProviderChange: (provider: EmbeddingProvider) => void
  onModelChange: (model: string, dimensions: number) => void
}

/**
 * Embeddings step: choose embedding provider, model, and dimensions.
 * Includes a prominent warning that this is permanent.
 */
export function StepEmbeddings({
  provider,
  model,
  dimensions,
  onProviderChange,
  onModelChange,
}: StepEmbeddingsProps) {
  const t = useTranslations('setup')

  const selectedProvider = EMBEDDING_OPTIONS.find((o) => o.id === provider)
  const models = selectedProvider?.models ?? []

  function handleProviderSwitch(id: EmbeddingProvider) {
    onProviderChange(id)
    const firstModel = EMBEDDING_OPTIONS.find((o) => o.id === id)?.models[0]
    if (firstModel) {
      onModelChange(firstModel.value, firstModel.dimensions)
    }
  }

  function handleModelSwitch(modelValue: string) {
    const found = models.find((m) => m.value === modelValue)
    if (found) {
      onModelChange(found.value, found.dimensions)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('embed_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('embed_desc')}</p>
      </div>

      {/* Warning banner */}
      <div
        className={cn(
          'flex gap-3 p-4 rounded-[var(--radius-md)]',
          'bg-[var(--color-warning)]/10 border border-[var(--color-warning)]/30'
        )}
        role="alert"
      >
        <svg
          className="shrink-0 text-[var(--color-warning)] mt-0.5"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <p className="text-sm text-[var(--color-warning)] leading-relaxed">
          {t('embed_warning')}
        </p>
      </div>

      {/* Embedding provider selector */}
      <div className="space-y-2">
        <label htmlFor="embed-provider" className="block text-sm font-medium text-[var(--color-text)]">
          {t('embed_provider')}
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup">
          {EMBEDDING_OPTIONS.map((opt) => {
            const isSelected = provider === opt.id
            return (
              <button
                key={opt.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => handleProviderSwitch(opt.id)}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)]',
                  'border transition-all text-left',
                  'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
                  isSelected
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 shadow-sm'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-muted)]'
                )}
              >
                <span className={cn(
                  'text-sm font-medium',
                  isSelected ? 'text-[var(--color-primary)]' : 'text-[var(--color-text)]'
                )}>
                  {opt.name}
                </span>
                {isSelected && (
                  <svg className="ml-auto shrink-0 text-[var(--color-primary)]" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Model selector */}
      <div className="space-y-2">
        <label htmlFor="embed-model" className="block text-sm font-medium text-[var(--color-text)]">
          {t('embed_model')}
        </label>
        <select
          id="embed-model"
          value={model}
          onChange={(e) => handleModelSwitch(e.target.value)}
          className={cn(
            'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
            'border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]',
            'text-sm input-focus-ring'
          )}
        >
          {models.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {/* Dimensions (read-only, derived from model) */}
      <div className="space-y-2">
        <label htmlFor="embed-dims" className="block text-sm font-medium text-[var(--color-text)]">
          {t('embed_dimensions')}
        </label>
        <input
          id="embed-dims"
          type="text"
          value={dimensions}
          readOnly
          className={cn(
            'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
            'border border-[var(--color-border)] bg-[var(--color-surface-elevated)] text-[var(--color-muted)]',
            'text-sm cursor-not-allowed'
          )}
        />
      </div>
    </div>
  )
}
