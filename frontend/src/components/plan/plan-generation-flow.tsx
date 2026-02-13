'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { usePipelineSSE } from '@/hooks/use-pipeline-sse'
import { PipelineViewer } from '@/components/pipeline/pipeline-viewer'
import { PlanTabs } from './plan-tabs'
import type { PlanGenerationRequest } from '@/types/plan'

const ACCESSIBILITY_PROFILES = [
  'standard',
  'tea',
  'tdah',
  'dyslexia',
  'low_vision',
  'hearing',
  'motor',
] as const

type WizardStep = 0 | 1 | 2 | 3

const STEP_COUNT = 4
const PROMPT_MAX_LENGTH = 2000

/**
 * Plan generation multi-step wizard.
 * Steps: 1) Subject & Grade, 2) Accessibility Profile, 3) Content/Prompt, 4) Review & Generate
 * Includes animated step indicator and inline validation.
 */
export function PlanGenerationFlow() {
  const t = useTranslations('plans')
  const tForm = useTranslations('plans.form')
  const tProfiles = useTranslations('plans.form.accessibility_profiles')
  const tWizard = useTranslations('plans.wizard')
  const tWizardShort = useTranslations('wizard_short')

  const {
    startGeneration,
    cancel,
    stages,
    plan,
    qualityReport,
    score,
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
  const [showSuccess, setShowSuccess] = useState(false)

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
    setShowSuccess(false)
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

  function validateStep(s: WizardStep): boolean {
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

  const showForm = !isRunning && !plan && !showSuccess
  const showPipeline = isRunning
  const showResult = !isRunning && plan !== null

  // After generation completes show success briefly
  if (showResult && !showSuccess) {
    setShowSuccess(true)
  }

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
            'rounded-[var(--radius-lg)] border',
            'bg-[var(--color-surface)] border-[var(--color-border)]',
            'overflow-hidden'
          )}
        >
          {/* Step indicator */}
          <div className="px-6 pt-6 pb-4">
            <div className="flex items-center justify-between mb-2">
              {stepLabels.map((label, i) => (
                <div key={i} className="flex items-center gap-2 flex-1">
                  <div className="flex items-center gap-2 min-w-0">
                    <motion.div
                      className={cn(
                        'flex items-center justify-center w-8 h-8 rounded-full',
                        'text-xs font-bold shrink-0 transition-colors'
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
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      {i < step ? <StepCheckIcon /> : i + 1}
                    </motion.div>
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
                      className={cn(
                        'flex-1 h-0.5 mx-2 rounded-full transition-colors',
                        i < step
                          ? 'bg-[var(--color-success)]'
                          : 'bg-[var(--color-border)]'
                      )}
                      aria-hidden="true"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step content */}
          <div className="px-6 pb-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Step 0: Subject & Grade */}
                {step === 0 && (
                  <div className="space-y-5">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label
                          htmlFor="plan-subject"
                          className="block text-sm font-semibold text-[var(--color-text)] mb-2"
                        >
                          {tForm('subject')}
                        </label>
                        <input
                          id="plan-subject"
                          type="text"
                          value={formData.subject}
                          onChange={(e) => updateField('subject', e.target.value)}
                          onBlur={() => validateStep(0)}
                          placeholder={tForm('subject_placeholder')}
                          className={cn(
                            'w-full rounded-[var(--radius-md)] border p-3',
                            'bg-[var(--color-bg)] border-[var(--color-border)]',
                            'text-[var(--color-text)] text-sm',
                            'placeholder:text-[var(--color-muted)]',
                            errors.subject && 'border-[var(--color-error)]'
                          )}
                        />
                        <FieldError message={errors.subject} />
                      </div>
                      <div>
                        <label
                          htmlFor="plan-grade"
                          className="block text-sm font-semibold text-[var(--color-text)] mb-2"
                        >
                          {tForm('grade')}
                        </label>
                        <input
                          id="plan-grade"
                          type="text"
                          value={formData.grade}
                          onChange={(e) => updateField('grade', e.target.value)}
                          onBlur={() => validateStep(0)}
                          placeholder={tForm('grade_placeholder')}
                          className={cn(
                            'w-full rounded-[var(--radius-md)] border p-3',
                            'bg-[var(--color-bg)] border-[var(--color-border)]',
                            'text-[var(--color-text)] text-sm',
                            'placeholder:text-[var(--color-muted)]',
                            errors.grade && 'border-[var(--color-error)]'
                          )}
                        />
                        <FieldError message={errors.grade} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 1: Accessibility Profile */}
                {step === 1 && (
                  <div className="space-y-4">
                    <p className="text-sm text-[var(--color-muted)]">
                      {tWizard('profile_description')}
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {ACCESSIBILITY_PROFILES.map((profile) => {
                        const selected = formData.accessibility_profile === profile
                        return (
                          <button
                            key={profile}
                            type="button"
                            onClick={() => updateField('accessibility_profile', profile)}
                            className={cn(
                              'flex items-center gap-3 p-4 rounded-[var(--radius-md)]',
                              'border text-left transition-all',
                              selected
                                ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 shadow-[var(--shadow-sm)]'
                                : 'border-[var(--color-border)] hover:border-[var(--color-primary)]/40'
                            )}
                          >
                            <PersonaAvatar profile={profile} selected={selected} />
                            <span
                              className={cn(
                                'text-sm font-medium',
                                selected
                                  ? 'text-[var(--color-primary)]'
                                  : 'text-[var(--color-text)]'
                              )}
                            >
                              {tProfiles(profile)}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Step 2: Content/Prompt */}
                {step === 2 && (
                  <div className="space-y-4">
                    <label
                      htmlFor="plan-prompt"
                      className="block text-sm font-semibold text-[var(--color-text)] mb-2"
                    >
                      {tForm('prompt')}
                    </label>
                    <textarea
                      id="plan-prompt"
                      value={formData.prompt}
                      onChange={(e) => updateField('prompt', e.target.value)}
                      onBlur={() => validateStep(2)}
                      placeholder={tForm('prompt_placeholder')}
                      rows={6}
                      maxLength={PROMPT_MAX_LENGTH}
                      className={cn(
                        'w-full rounded-[var(--radius-md)] border p-3',
                        'bg-[var(--color-bg)] border-[var(--color-border)]',
                        'text-[var(--color-text)] text-sm',
                        'placeholder:text-[var(--color-muted)]',
                        'resize-y',
                        errors.prompt && 'border-[var(--color-error)]'
                      )}
                    />
                    <div className="flex items-center justify-between mt-1.5">
                      <FieldError message={errors.prompt} />
                      <span
                        className={cn(
                          'text-xs ml-auto',
                          formData.prompt.length > PROMPT_MAX_LENGTH * 0.9
                            ? 'text-[var(--color-warning)]'
                            : 'text-[var(--color-muted)]'
                        )}
                        aria-live="polite"
                      >
                        {formData.prompt.length} / {PROMPT_MAX_LENGTH}
                      </span>
                    </div>
                  </div>
                )}

                {/* Step 3: Review & Generate */}
                {step === 3 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-semibold text-[var(--color-text)]">
                      {tWizard('review_title')}
                    </h3>
                    <div
                      className={cn(
                        'rounded-[var(--radius-md)] border border-[var(--color-border)]',
                        'divide-y divide-[var(--color-border)]'
                      )}
                    >
                      <ReviewRow label={tForm('subject')} value={formData.subject} />
                      <ReviewRow label={tForm('grade')} value={formData.grade} />
                      <ReviewRow
                        label={tForm('accessibility_profile')}
                        value={tProfiles(formData.accessibility_profile)}
                      />
                      <ReviewRow
                        label={tForm('prompt')}
                        value={formData.prompt}
                        multiline
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

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
                  'hover:bg-[var(--color-surface-elevated)] transition-colors',
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
                    'hover:bg-[var(--color-primary-hover)] transition-colors'
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
                    'px-6 py-2.5 rounded-[var(--radius-md)]',
                    'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                    'text-sm font-semibold',
                    'hover:bg-[var(--color-primary-hover)] transition-colors',
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
        <div className="space-y-6">
          {/* Success celebration */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn(
              'flex items-center gap-3 p-4 rounded-[var(--radius-lg)]',
              'bg-[var(--color-success)]/10 border border-[var(--color-success)]/20'
            )}
          >
            <div
              className="flex items-center justify-center w-10 h-10 rounded-full bg-[var(--color-success)]"
              aria-hidden="true"
            >
              <SuccessCheckIcon />
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--color-success)]">
                {t('generation_complete')}
              </p>
              {score !== null && (
                <p className="text-xs text-[var(--color-muted)] mt-0.5">
                  {t('quality_score')}: {score}/100
                </p>
              )}
            </div>
          </motion.div>

          <PlanTabs plan={plan} qualityReport={qualityReport} score={score} />

          <div className="flex justify-center">
            <button
              type="button"
              onClick={resetWizard}
              className={cn(
                'px-6 py-2 rounded-[var(--radius-md)]',
                'border border-[var(--color-border)] text-[var(--color-text)]',
                'text-sm font-medium hover:bg-[var(--color-surface-elevated)]'
              )}
            >
              {t('create')}
            </button>
          </div>
        </div>
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

/* ===== Sub-components ===== */

function FieldError({ message }: { message?: string }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.p
          initial={{ opacity: 0, y: -4, height: 0 }}
          animate={{ opacity: 1, y: 0, height: 'auto' }}
          exit={{ opacity: 0, y: -4, height: 0 }}
          className="text-xs text-[var(--color-error)] mt-1.5"
          role="alert"
        >
          {message}
        </motion.p>
      )}
    </AnimatePresence>
  )
}

function ReviewRow({
  label,
  value,
  multiline = false,
}: {
  label: string
  value: string
  multiline?: boolean
}) {
  return (
    <div className="flex gap-4 px-4 py-3">
      <span className="text-sm font-medium text-[var(--color-muted)] w-32 shrink-0">
        {label}
      </span>
      <span
        className={cn(
          'text-sm text-[var(--color-text)]',
          multiline && 'whitespace-pre-wrap'
        )}
      >
        {value}
      </span>
    </div>
  )
}

/** CSS-based persona avatar using theme custom properties for high-contrast compliance */
function PersonaAvatar({
  profile,
  selected,
}: {
  profile: string
  selected: boolean
}) {
  const colors: Record<string, string> = {
    standard: 'var(--color-primary)',
    tea: 'var(--color-success)',
    tdah: 'var(--color-warning)',
    dyslexia: 'var(--color-primary)',
    low_vision: 'var(--color-primary)',
    hearing: 'var(--color-secondary)',
    motor: 'var(--color-primary)',
  }
  const color = colors[profile] ?? 'var(--color-primary)'

  return (
    <div
      className={cn(
        'flex items-center justify-center w-10 h-10 rounded-full',
        'text-xs font-bold transition-transform',
        selected && 'scale-110'
      )}
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
        color: color,
      }}
      aria-hidden="true"
    >
      {profile.slice(0, 2).toUpperCase()}
    </div>
  )
}

/** Short labels for mobile display -- resolved from i18n at render time via tWizardShort */

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

function SuccessCheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M5 10l3.5 3.5L15 7"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
