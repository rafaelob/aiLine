'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import type { Variants } from 'motion/react'
import { cn } from '@/lib/cn'
import { SetupStepIndicator } from './setup-step-indicator'
import { StepWelcome } from './steps/step-welcome'
import { StepAiProvider } from './steps/step-ai-provider'
import { StepEmbeddings } from './steps/step-embeddings'
import { StepAgentModels } from './steps/step-agent-models'
import { StepInfrastructure } from './steps/step-infrastructure'
import { StepSecurity } from './steps/step-security'
import { StepReview } from './steps/step-review'
import { DEFAULT_CONFIG, TOTAL_STEPS } from './setup-types'
import type { SetupConfig, LlmProvider, EmbeddingProvider } from './setup-types'

interface SetupWizardProps {
  locale: string
}

type ApplyStatus = 'idle' | 'writing' | 'done' | 'error'

/**
 * Main setup wizard orchestrator.
 * Manages step navigation, state, validation, and API calls.
 */
export function SetupWizard({ locale }: SetupWizardProps) {
  const t = useTranslations('setup')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const [step, setStep] = useState(0)
  const [direction, setDirection] = useState(1)
  const [config, setConfig] = useState<SetupConfig>({
    ...DEFAULT_CONFIG,
    language: locale,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [applying, setApplying] = useState(false)
  const [applyStatus, setApplyStatus] = useState<ApplyStatus>('idle')

  const updateField = useCallback(
    (field: keyof SetupConfig, value: string | number) => {
      setConfig((prev) => ({ ...prev, [field]: value }))
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    },
    []
  )

  /** Validate the current step. Returns true if valid. */
  const validateStep = useCallback((): boolean => {
    const newErrors: Record<string, string> = {}

    if (step === 1) {
      if (!config.llmProvider) {
        newErrors.llmProvider = t('select_provider')
      }
      if (config.llmProvider && !config.llmApiKey.trim()) {
        newErrors.llmApiKey = t('field_required')
      }
    }

    if (step === 4) {
      if (!config.databaseUrl.trim()) newErrors.databaseUrl = t('field_required')
      if (!config.redisUrl.trim()) newErrors.redisUrl = t('field_required')
      if (!config.apiPort.trim()) newErrors.apiPort = t('field_required')
      if (!config.frontendPort.trim()) newErrors.frontendPort = t('field_required')
    }

    if (step === 5) {
      if (!config.jwtSecret.trim()) newErrors.jwtSecret = t('field_required')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [step, config, t])

  const goNext = useCallback(() => {
    if (!validateStep()) return
    if (step < TOTAL_STEPS - 1) {
      setDirection(1)
      setStep((s) => s + 1)
    }
  }, [step, validateStep])

  const goBack = useCallback(() => {
    if (step > 0) {
      setDirection(-1)
      setStep((s) => s - 1)
    }
  }, [step])

  const handleApply = useCallback(async () => {
    setApplying(true)
    setApplyStatus('writing')
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8011'
      const res = await fetch(`${apiBase}/api/v1/setup/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (res.ok) {
        setApplyStatus('done')
      } else {
        setApplyStatus('error')
      }
    } catch {
      setApplyStatus('error')
    } finally {
      setApplying(false)
    }
  }, [config])

  const isLastStep = step === TOTAL_STEPS - 1

  /** Slide animation variants */
  const slideVariants: Variants | undefined = noMotion
    ? undefined
    : {
        enter: (dir: number) => ({
          x: dir > 0 ? 60 : -60,
          opacity: 0,
        }),
        center: {
          x: 0,
          opacity: 1,
        },
        exit: (dir: number) => ({
          x: dir > 0 ? -60 : 60,
          opacity: 0,
        }),
      }

  return (
    <div className="space-y-6">
      {/* Logo header */}
      <div className="text-center mb-2">
        <h1 className="text-lg font-bold text-[var(--color-text)]">
          {t('title')}
        </h1>
        <p className="text-xs text-[var(--color-muted)]">{t('subtitle')}</p>
      </div>

      {/* Step indicator */}
      <SetupStepIndicator currentStep={step} />

      {/* Step content with animated transitions */}
      <div
        className={cn(
          'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
          'bg-[var(--color-surface)] p-6 sm:p-8',
          'shadow-[var(--shadow-md)]',
          'min-h-[360px] relative overflow-hidden'
        )}
      >
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={step}
            custom={direction}
            variants={slideVariants}
            initial={noMotion ? undefined : 'enter'}
            animate={noMotion ? undefined : 'center'}
            exit={noMotion ? undefined : 'exit'}
            transition={
              noMotion ? undefined : { type: 'spring', stiffness: 300, damping: 30, duration: 0.3 }
            }
          >
            {step === 0 && (
              <StepWelcome
                language={config.language}
                onLanguageChange={(lang) => updateField('language', lang)}
              />
            )}
            {step === 1 && (
              <StepAiProvider
                provider={config.llmProvider}
                apiKey={config.llmApiKey}
                onProviderChange={(p: LlmProvider) => updateField('llmProvider', p)}
                onApiKeyChange={(k) => updateField('llmApiKey', k)}
                errors={errors}
              />
            )}
            {step === 2 && (
              <StepEmbeddings
                provider={config.embeddingProvider}
                model={config.embeddingModel}
                dimensions={config.embeddingDimensions}
                onProviderChange={(p: EmbeddingProvider) => updateField('embeddingProvider', p)}
                onModelChange={(m, d) => {
                  setConfig((prev) => ({
                    ...prev,
                    embeddingModel: m,
                    embeddingDimensions: d,
                  }))
                }}
              />
            )}
            {step === 3 && (
              <StepAgentModels
                config={config}
                onModelChange={(field, value) => updateField(field, value)}
              />
            )}
            {step === 4 && (
              <StepInfrastructure
                config={config}
                onChange={(field, value) => updateField(field, value)}
                errors={errors}
              />
            )}
            {step === 5 && (
              <StepSecurity
                config={config}
                onChange={(field, value) => updateField(field, value)}
                errors={errors}
              />
            )}
            {step === 6 && (
              <StepReview
                config={config}
                applying={applying}
                applyStatus={applyStatus}
                onApply={handleApply}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={goBack}
          disabled={step === 0}
          className={cn(
            'px-5 py-2.5 rounded-[var(--radius-sm)]',
            'text-sm font-medium',
            'border border-[var(--color-border)] text-[var(--color-text)]',
            'hover:bg-[var(--color-surface-elevated)]',
            'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
            'disabled:opacity-30 disabled:cursor-not-allowed',
            'transition-colors btn-press'
          )}
          aria-label={t('back')}
        >
          {t('back')}
        </button>

        {!isLastStep && (
          <button
            type="button"
            onClick={goNext}
            className={cn(
              'px-5 py-2.5 rounded-[var(--radius-sm)]',
              'text-sm font-semibold',
              'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
              'hover:bg-[var(--color-primary-hover)]',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
              'transition-colors btn-press'
            )}
            aria-label={t('next')}
          >
            {t('next')}
          </button>
        )}
      </div>
    </div>
  )
}
