'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { usePipelineSSE } from '@/hooks/use-pipeline-sse'
import { PipelineViewer } from '@/components/pipeline/pipeline-viewer'
import { WizardSteps } from './wizard-steps'
import { PlanResultDisplay } from './plan-result-display'
import type { PlanGenerationRequest } from '@/types/plan'
import { DEMO_PROMPT, DEMO_GRADE, DEMO_SUBJECT, DEMO_PROFILE } from '@/lib/demo-data'
import { useDemoStore } from '@/stores/demo-store'

type WizardStep = 0 | 1 | 2 | 3

const STEP_COUNT = 4

/**
 * Plan generation multi-step wizard.
 * Steps: 1) Subject & Grade, 2) Accessibility Profile, 3) Content/Prompt, 4) Review & Generate
 * Includes animated step indicator and inline validation.
 */
export function PlanGenerationFlow() {
  const t = useTranslations('plans')
  const tWizard = useTranslations('plans.wizard')
  const tWizardShort = useTranslations('wizard_short')

  const {
    startGeneration,
    cancel,
    runId,
    stages,
    plan,
    qualityReport,
    score,
    scorecard,
    isRunning,
    error,
  } = usePipelineSSE()

  const [step, setStep] = useState<WizardStep>(0)
  const [formData, setFormData] = useState<PlanGenerationRequest>({
    prompt: '',
    grade: '',
    subject: '',
    accessibility_profile: 'standard',
    locale: 'pt-BR',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const stepContentRef = useRef<HTMLDivElement>(null)

  const resetWizard = useCallback(() => {
    setStep(0)
    setFormData({
      prompt: '',
      grade: '',
      subject: '',
      accessibility_profile: 'standard',
      locale: 'pt-BR',
    })
    setErrors({})
  }, [])

  const handleSubmit = useCallback(
    async () => {
      await startGeneration(formData)
    },
    [formData, startGeneration]
  )

  function updateField<K extends keyof PlanGenerationRequest>(
    key: K,
    value: PlanGenerationRequest[K]
  ) {
    setFormData((prev) => ({ ...prev, [key]: value }))
    // Clear error on change
    if (errors[key]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }
  }

  function validateStep(s: number): boolean {
    const newErrors: Record<string, string> = {}
    if (s === 0) {
      if (!formData.subject.trim()) newErrors.subject = tWizard('required')
      if (!formData.grade.trim()) newErrors.grade = tWizard('required')
    }
    if (s === 2) {
      if (!formData.prompt.trim()) newErrors.prompt = tWizard('required')
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function goNext() {
    if (validateStep(step)) {
      if (step < STEP_COUNT - 1) {
        setStep((s) => (s + 1) as WizardStep)
      }
    }
  }

  function goBack() {
    if (step > 0) {
      setStep((s) => (s - 1) as WizardStep)
    }
  }

  // Move focus to step content on step change for screen reader users
  useEffect(() => {
    if (stepContentRef.current) {
      stepContentRef.current.focus({ preventScroll: true })
    }
  }, [step])

  // Auto-fill from demo mode (deferred to avoid React Compiler cascading-render warning)
  const demoInitRef = useRef(false)
  useEffect(() => {
    if (demoInitRef.current) return
    const params = new URLSearchParams(window.location.search)
    if (params.get('demo') === 'true') {
      demoInitRef.current = true
      queueMicrotask(() => {
        setFormData((prev) => ({
          ...prev,
          subject: DEMO_SUBJECT,
          grade: DEMO_GRADE,
          accessibility_profile: DEMO_PROFILE,
          prompt: DEMO_PROMPT,
        }))
        setStep(3 as WizardStep)
        useDemoStore.getState().startDemo()
      })
    }
  }, [])

  const showForm = !isRunning && !plan
  const showPipeline = isRunning
  const showResult = !isRunning && plan !== null

  const stepLabels = [
    tWizard('step_subject'),
    tWizard('step_profile'),
    tWizard('step_prompt'),
    tWizard('step_review'),
  ]

  return (
    <div className="space-y-8">
      {/* Wizard form */}
      {showForm && (
        <div
          className={cn(
            'rounded-xl glass',
            'overflow-hidden'
          )}
          role="group"
          aria-roledescription="wizard"
          aria-label={tWizard('wizard_label')}
        >
          {/* Step indicator */}
          <div className="px-6 pt-6 pb-4">
            <nav aria-label={`Step ${step + 1} of ${STEP_COUNT}`}>
              <ol className="flex items-center justify-between mb-2" role="list">
                {stepLabels.map((label, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 flex-1"
                    aria-current={i === step ? 'step' : undefined}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="relative flex items-center justify-center w-8 h-8 shrink-0">
                        {i === step && (
                          <span
                            className="absolute inset-0 rounded-full bg-[var(--color-primary)] animate-ring-pulse motion-reduce:hidden"
                            aria-hidden="true"
                          />
                        )}
                        <motion.div
                          className={cn(
                            'relative flex items-center justify-center w-8 h-8 rounded-full',
                            'text-xs font-bold',
                            i === step && 'shadow-[var(--shadow-glow)]'
                          )}
                          animate={{
                            backgroundColor:
                              i < step
                                ? 'var(--color-success)'
                                : i === step
                                  ? 'var(--color-primary)'
                                  : 'var(--color-surface-elevated)',
                            color:
                              i <= step
                                ? 'var(--color-on-primary)'
                                : 'var(--color-muted)',
                            scale: i === step ? 1.1 : 1,
                          }}
                          transition={{ duration: 0.3, type: 'spring', stiffness: 300 }}
                          aria-hidden="true"
                        >
                          {i < step ? <StepCheckIcon /> : i + 1}
                        </motion.div>
                      </div>
                      <span
                        className={cn(
                          'text-xs font-medium truncate',
                          i === step
                            ? 'text-[var(--color-text)]'
                            : 'text-[var(--color-muted)]'
                        )}
                      >
                        <span className="sm:hidden">{tWizardShort(`step_${i}`)}</span>
                        <span className="hidden sm:inline">{label}</span>
                      </span>
                    </div>
                    {i < STEP_COUNT - 1 && (
                      <div
                        className="flex-1 h-0.5 mx-2 rounded-full bg-[var(--color-border)] overflow-hidden"
                        aria-hidden="true"
                      >
                        <motion.div
                          className="h-full rounded-full"
                          style={{ background: 'linear-gradient(90deg, var(--color-success), var(--color-primary))' }}
                          initial={{ width: '0%' }}
                          animate={{ width: i < step ? '100%' : '0%' }}
                          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                        />
                      </div>
                    )}
                  </li>
                ))}
              </ol>
            </nav>
            {/* Live region for screen readers announcing step changes */}
            <div className="sr-only" aria-live="polite" aria-atomic="true">
              {`Step ${step + 1} of ${STEP_COUNT}: ${stepLabels[step]}`}
            </div>
          </div>

          {/* Step content */}
          <div ref={stepContentRef} tabIndex={-1} className="px-6 pb-6 outline-none">
            <WizardSteps
              step={step}
              formData={formData}
              errors={errors}
              onUpdateField={updateField}
              onValidateStep={validateStep}
            />

            {/* Navigation buttons */}
            <div className="flex items-center justify-between mt-6">
              <button
                type="button"
                onClick={goBack}
                disabled={step === 0}
                className={cn(
                  'px-5 py-2.5 rounded-[var(--radius-md)]',
                  'text-sm font-medium text-[var(--color-text)]',
                  'border border-[var(--color-border)]',
                  'hover:bg-[var(--color-surface-elevated)] transition-colors active:scale-95',
                  'disabled:opacity-40 disabled:cursor-not-allowed'
                )}
              >
                {tWizard('back')}
              </button>

              {step < STEP_COUNT - 1 ? (
                <button
                  type="button"
                  onClick={goNext}
                  className={cn(
                    'px-5 py-2.5 rounded-[var(--radius-md)]',
                    'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                    'text-sm font-medium',
                    'hover:bg-[var(--color-primary-hover)] transition-colors active:scale-95'
                  )}
                >
                  {tWizard('next')}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isRunning}
                  className={cn(
                    'px-6 py-2.5 rounded-[var(--radius-md)] btn-shimmer',
                    'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                    'text-sm font-semibold',
                    'hover:bg-[var(--color-primary-hover)] transition-colors active:scale-95',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {t('generate')}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline viewer during generation */}
      {showPipeline && (
        <div className="space-y-4">
          <PipelineViewer stages={stages} isRunning={isRunning} error={error} />
          <div className="flex justify-center">
            <button
              type="button"
              onClick={cancel}
              className={cn(
                'px-6 py-2 rounded-[var(--radius-md)]',
                'border border-[var(--color-error)] text-[var(--color-error)]',
                'text-sm font-medium hover:bg-[var(--color-error)]/5'
              )}
            >
              {t('cancel')}
            </button>
          </div>
        </div>
      )}

      {/* Plan result with celebration */}
      {showResult && plan && (
        <PlanResultDisplay
          plan={plan}
          qualityReport={qualityReport}
          score={score}
          scorecard={scorecard}
          runId={runId}
          onReset={resetWizard}
        />
      )}

      {/* Error state when not running and no plan */}
      {!isRunning && !plan && error && (
        <div
          role="alert"
          className={cn(
            'rounded-[var(--radius-md)] p-4 text-center',
            'bg-[var(--color-error)]/10 text-[var(--color-error)]'
          )}
        >
          <p className="text-sm">{error}</p>
          <button
            type="button"
            onClick={resetWizard}
            className={cn(
              'mt-3 px-4 py-2 rounded-[var(--radius-md)]',
              'border border-[var(--color-error)] text-sm',
              'hover:bg-[var(--color-error)]/5'
            )}
          >
            {t('try_again')}
          </button>
        </div>
      )}
    </div>
  )
}

/* ===== Local Sub-components ===== */

function StepCheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path
        d="M3 7l3 3 5-5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
