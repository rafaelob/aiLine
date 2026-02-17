'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { LlmProvider } from '../setup-types'
import { LLM_PROVIDERS } from '../setup-types'

interface StepAiProviderProps {
  provider: LlmProvider | ''
  apiKey: string
  onProviderChange: (provider: LlmProvider) => void
  onApiKeyChange: (key: string) => void
  errors: Record<string, string>
}

/**
 * AI Provider step: select LLM provider and enter API key.
 */
export function StepAiProvider({
  provider,
  apiKey,
  onProviderChange,
  onApiKeyChange,
  errors,
}: StepAiProviderProps) {
  const t = useTranslations('setup')
  const [showKey, setShowKey] = useState(false)
  const [validating, setValidating] = useState(false)
  const [keyStatus, setKeyStatus] = useState<'idle' | 'valid' | 'invalid'>('idle')

  const handleValidate = useCallback(async () => {
    if (!apiKey || !provider) return
    setValidating(true)
    setKeyStatus('idle')
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8011'
      const res = await fetch(`${apiBase}/api/v1/setup/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey }),
      })
      setKeyStatus(res.ok ? 'valid' : 'invalid')
    } catch {
      setKeyStatus('invalid')
    } finally {
      setValidating(false)
    }
  }, [apiKey, provider])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('ai_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('ai_desc')}</p>
      </div>

      {/* Provider cards */}
      <fieldset>
        <legend className="sr-only">{t('ai_title')}</legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup">
          {LLM_PROVIDERS.map((p) => {
            const isSelected = provider === p.id
            return (
              <button
                key={p.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => {
                  onProviderChange(p.id)
                  setKeyStatus('idle')
                }}
                className={cn(
                  'flex items-start gap-3 p-4 rounded-[var(--radius-md)]',
                  'border transition-all text-left',
                  'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
                  isSelected
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 shadow-sm'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-muted)]'
                )}
              >
                {/* Provider logo placeholder */}
                <span
                  className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0"
                  style={{ backgroundColor: p.color }}
                  aria-hidden="true"
                >
                  {p.letter}
                </span>
                <div className="flex-1 min-w-0">
                  <span className={cn(
                    'text-sm font-semibold block',
                    isSelected ? 'text-[var(--color-primary)]' : 'text-[var(--color-text)]'
                  )}>
                    {t(p.nameKey)}
                  </span>
                  <span className="text-xs text-[var(--color-muted)] mt-0.5 block">
                    {t(p.descKey)}
                  </span>
                </div>
                {isSelected && (
                  <svg className="shrink-0 text-[var(--color-primary)] mt-1" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
        {errors.llmProvider && (
          <p className="mt-2 text-xs text-[var(--color-error)]" role="alert">{errors.llmProvider}</p>
        )}
      </fieldset>

      {/* API Key input (shown when provider is selected) */}
      {provider && (
        <div className="space-y-2">
          <label htmlFor="api-key" className="block text-sm font-medium text-[var(--color-text)]">
            {t('api_key')}
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                id="api-key"
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  onApiKeyChange(e.target.value)
                  setKeyStatus('idle')
                }}
                placeholder={t('api_key_placeholder')}
                autoComplete="off"
                className={cn(
                  'w-full px-3 py-2.5 pr-10 rounded-[var(--radius-sm)]',
                  'border bg-[var(--color-surface)] text-[var(--color-text)]',
                  'text-sm placeholder:text-[var(--color-muted)]/60',
                  'input-focus-ring',
                  errors.llmApiKey ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'
                )}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--color-muted)] hover:text-[var(--color-text)]"
                aria-label={showKey ? t('hide_key') : t('show_key')}
              >
                {showKey ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" /><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                )}
              </button>
            </div>
            <button
              type="button"
              onClick={handleValidate}
              disabled={!apiKey || validating}
              className={cn(
                'px-4 py-2.5 rounded-[var(--radius-sm)] text-sm font-medium',
                'border border-[var(--color-primary)] text-[var(--color-primary)]',
                'hover:bg-[var(--color-primary)]/5',
                'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-colors'
              )}
            >
              {validating ? t('validating_key') : t('validate_key')}
            </button>
          </div>
          {errors.llmApiKey && (
            <p className="text-xs text-[var(--color-error)]" role="alert">{errors.llmApiKey}</p>
          )}
          {keyStatus === 'valid' && (
            <p className="text-xs text-[var(--color-success)] flex items-center gap-1" role="status">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12" /></svg>
              {t('key_valid')}
            </p>
          )}
          {keyStatus === 'invalid' && (
            <p className="text-xs text-[var(--color-error)] flex items-center gap-1" role="alert">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              {t('key_invalid')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
