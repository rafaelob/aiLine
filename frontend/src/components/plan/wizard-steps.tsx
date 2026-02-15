'use client'

import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
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

const PROMPT_MAX_LENGTH = 2000

interface WizardStepsProps {
  step: number
  formData: PlanGenerationRequest
  errors: Record<string, string>
  onUpdateField: <K extends keyof PlanGenerationRequest>(
    key: K,
    value: PlanGenerationRequest[K]
  ) => void
  onValidateStep: (s: number) => boolean
}

/**
 * Wizard step content renderer. Displays the appropriate form fields
 * for each step of the plan generation wizard.
 */
export function WizardSteps({
  step,
  formData,
  errors,
  onUpdateField,
  onValidateStep,
}: WizardStepsProps) {
  const tForm = useTranslations('plans.form')
  const tProfiles = useTranslations('plans.form.accessibility_profiles')
  const tWizard = useTranslations('plans.wizard')

  return (
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
                  onChange={(e) => onUpdateField('subject', e.target.value)}
                  onBlur={() => onValidateStep(0)}
                  placeholder={tForm('subject_placeholder')}
                  autoComplete="off"
                  aria-required={true}
                  aria-invalid={!!errors.subject}
                  aria-describedby={errors.subject ? 'subject-error' : undefined}
                  className={cn(
                    'w-full rounded-[var(--radius-md)] border p-3 input-focus-ring',
                    'bg-[var(--color-bg)] border-[var(--color-border)]',
                    'text-[var(--color-text)] text-sm',
                    'placeholder:text-[var(--color-muted)]',
                    'focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:outline-none',
                    'transition-all duration-200',
                    errors.subject && 'border-[var(--color-error)]'
                  )}
                />
                <FieldError id="subject-error" message={errors.subject} />
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
                  onChange={(e) => onUpdateField('grade', e.target.value)}
                  onBlur={() => onValidateStep(0)}
                  placeholder={tForm('grade_placeholder')}
                  autoComplete="off"
                  aria-required={true}
                  aria-invalid={!!errors.grade}
                  aria-describedby={errors.grade ? 'grade-error' : undefined}
                  className={cn(
                    'w-full rounded-[var(--radius-md)] border p-3 input-focus-ring',
                    'bg-[var(--color-bg)] border-[var(--color-border)]',
                    'text-[var(--color-text)] text-sm',
                    'placeholder:text-[var(--color-muted)]',
                    'focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:outline-none',
                    'transition-all duration-200',
                    errors.grade && 'border-[var(--color-error)]'
                  )}
                />
                <FieldError id="grade-error" message={errors.grade} />
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
            <div
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
              role="radiogroup"
              aria-label={tForm('accessibility_profile')}
              onKeyDown={(e) => {
                const keys = ['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft']
                if (!keys.includes(e.key)) return
                e.preventDefault()
                const idx = ACCESSIBILITY_PROFILES.indexOf(
                  formData.accessibility_profile as typeof ACCESSIBILITY_PROFILES[number]
                )
                const dir = e.key === 'ArrowDown' || e.key === 'ArrowRight' ? 1 : -1
                const next = (idx + dir + ACCESSIBILITY_PROFILES.length) % ACCESSIBILITY_PROFILES.length
                onUpdateField('accessibility_profile', ACCESSIBILITY_PROFILES[next])
                // Focus the newly selected radio
                const container = e.currentTarget
                const radios = container.querySelectorAll<HTMLElement>('[role="radio"]')
                radios[next]?.focus()
              }}
            >
              {ACCESSIBILITY_PROFILES.map((profile) => {
                const selected = formData.accessibility_profile === profile
                return (
                  <button
                    key={profile}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => onUpdateField('accessibility_profile', profile)}
                    className={cn(
                      'relative flex items-center gap-3 p-4 rounded-[var(--radius-md)]',
                      'border text-left transition-all',
                      selected
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 shadow-[var(--shadow-sm)] scale-[1.02]'
                        : 'border-[var(--color-border)] hover:border-[var(--color-primary)]/40'
                    )}
                  >
                    {selected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-primary)]"
                        aria-hidden="true"
                      >
                        <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
                          <path d="M3 7l3 3 5-5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </motion.div>
                    )}
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
              onChange={(e) => onUpdateField('prompt', e.target.value)}
              onBlur={() => onValidateStep(2)}
              placeholder={tForm('prompt_placeholder')}
              rows={6}
              maxLength={PROMPT_MAX_LENGTH}
              aria-required={true}
              aria-invalid={!!errors.prompt}
              aria-describedby={errors.prompt ? 'prompt-error' : undefined}
              className={cn(
                'w-full rounded-[var(--radius-md)] border p-3 input-focus-ring',
                'bg-[var(--color-bg)] border-[var(--color-border)]',
                'text-[var(--color-text)] text-sm',
                'placeholder:text-[var(--color-muted)]',
                'focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:outline-none',
                'transition-all duration-200',
                'resize-y',
                errors.prompt && 'border-[var(--color-error)]'
              )}
            />
            <div className="flex items-center justify-between mt-1.5">
              <FieldError id="prompt-error" message={errors.prompt} />
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
            <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)]">
              <div
                className="px-4 py-2 text-xs font-semibold text-[var(--color-on-primary)]"
                style={{ background: 'var(--gradient-hero)' }}
              >
                {tWizard('review_title')}
              </div>
              <div className="divide-y divide-[var(--color-border)]">
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
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

/* ===== Helper Sub-components ===== */

function FieldError({ id, message }: { id?: string; message?: string }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.p
          id={id}
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
