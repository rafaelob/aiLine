'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { SetupConfig } from '../setup-types'
import { AGENT_MODELS, MODEL_OPTIONS } from '../setup-types'

interface StepAgentModelsProps {
  config: SetupConfig
  onModelChange: (field: keyof SetupConfig, value: string) => void
}

/**
 * Agent Models step: configure which AI model each agent uses.
 * Provides dropdowns with smart defaults based on the selected LLM provider.
 */
export function StepAgentModels({ config, onModelChange }: StepAgentModelsProps) {
  const t = useTranslations('setup')

  const providerKey = config.llmProvider || 'anthropic'
  const options = MODEL_OPTIONS[providerKey] ?? MODEL_OPTIONS.anthropic

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{t('models_title')}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{t('models_desc')}</p>
      </div>

      <div className="space-y-4">
        {AGENT_MODELS.map((agent) => {
          const value = config[agent.id] as string
          return (
            <div
              key={agent.id}
              className={cn(
                'p-4 rounded-[var(--radius-md)]',
                'border border-[var(--color-border)] bg-[var(--color-surface)]'
              )}
            >
              <label htmlFor={`agent-${agent.id}`} className="block text-sm font-semibold text-[var(--color-text)]">
                {t(agent.nameKey)}
              </label>
              <p className="text-xs text-[var(--color-muted)] mt-0.5 mb-3">
                {t(agent.descKey)}
              </p>
              <select
                id={`agent-${agent.id}`}
                value={value}
                onChange={(e) => onModelChange(agent.id, e.target.value)}
                className={cn(
                  'w-full px-3 py-2.5 rounded-[var(--radius-sm)]',
                  'border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)]',
                  'text-sm input-focus-ring'
                )}
              >
                {options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )
        })}
      </div>
    </div>
  )
}
