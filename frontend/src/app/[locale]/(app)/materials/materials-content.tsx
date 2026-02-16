'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface Material {
  id: string
  teacher_id: string
  subject: string
  title: string
  content: string
  tags: string[]
  created_at: string
}

const subjectColors: Record<string, string> = {
  math: 'var(--color-primary)',
  science: 'var(--color-success)',
  language: 'var(--color-secondary)',
  history: '#d97706',
  geography: '#0891b2',
}

function getSubjectColor(subject: string): string {
  const key = subject.toLowerCase()
  for (const [k, v] of Object.entries(subjectColors)) {
    if (key.includes(k)) return v
  }
  return 'var(--color-primary)'
}

export function MaterialsContent() {
  const t = useTranslations('materials')
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState('')
  const [content, setContent] = useState('')
  const [tags, setTags] = useState('')

  const fetchMaterials = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/materials`, { headers: getAuthHeaders() })
      if (res.ok) {
        const data: Material[] = await res.json()
        setMaterials(data)
      }
    } catch {
      /* network error — silent for now */
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMaterials()
  }, [fetchMaterials])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setErrorMsg('')
    try {
      const res = await fetch(`${API_BASE}/materials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          teacher_id: 'dev-teacher',
          subject,
          title,
          content,
          tags: tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean),
        }),
      })
      if (!res.ok) throw new Error('Upload failed')
      setSuccessMsg(t('success'))
      setTitle('')
      setSubject('')
      setContent('')
      setTags('')
      setShowForm(false)
      setTimeout(() => setSuccessMsg(''), 3000)
      fetchMaterials()
    } catch {
      setErrorMsg(t('error'))
    } finally {
      setSubmitting(false)
    }
  }

  const resetForm = () => {
    setShowForm(false)
    setTitle('')
    setSubject('')
    setContent('')
    setTags('')
    setErrorMsg('')
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      {/* Toasts */}
      {successMsg && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          className="glass rounded-xl border border-green-500/30 p-3 text-sm text-green-700 dark:text-green-300"
          role="status"
        >
          {successMsg}
        </motion.div>
      )}
      {errorMsg && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-xl border border-red-500/30 p-3 text-sm text-red-700 dark:text-red-300"
          role="alert"
        >
          {errorMsg}
        </motion.div>
      )}

      {/* Upload button */}
      {!showForm && (
        <motion.div variants={itemVariants}>
          <button
            onClick={() => setShowForm(true)}
            className={cn(
              'inline-flex items-center gap-2 px-6 py-3',
              'rounded-xl btn-shimmer',
              'text-sm font-semibold',
              'text-[var(--color-on-primary)]',
              'shadow-[var(--shadow-md)]',
              'hover:shadow-[var(--shadow-lg)] hover:scale-[1.02]',
              'transition-all duration-300'
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            <UploadIcon />
            {t('upload')}
          </button>
        </motion.div>
      )}

      {/* Upload form */}
      {showForm && (
        <motion.form
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 24 }}
          onSubmit={handleSubmit}
          className="glass rounded-2xl p-6 space-y-4 border border-[var(--color-border)]"
        >
          <div className="space-y-1">
            <label htmlFor="material-title" className="text-sm font-medium text-[var(--color-text)]">
              {t('field_title')}
            </label>
            <input
              id="material-title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full glass rounded-[var(--radius-md)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text)] bg-[var(--color-bg)]"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="material-subject" className="text-sm font-medium text-[var(--color-text)]">
              {t('field_subject')}
            </label>
            <input
              id="material-subject"
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full glass rounded-[var(--radius-md)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text)] bg-[var(--color-bg)]"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="material-content" className="text-sm font-medium text-[var(--color-text)]">
              {t('field_content')}
            </label>
            <textarea
              id="material-content"
              required
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full glass rounded-[var(--radius-md)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text)] bg-[var(--color-bg)] resize-y"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="material-tags" className="text-sm font-medium text-[var(--color-text)]">
              {t('field_tags')}
            </label>
            <input
              id="material-tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full glass rounded-[var(--radius-md)] border border-[var(--color-border)] p-3 text-sm text-[var(--color-text)] bg-[var(--color-bg)]"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className={cn(
                'inline-flex items-center gap-2 px-6 py-3',
                'rounded-xl btn-shimmer',
                'text-sm font-semibold',
                'text-[var(--color-on-primary)]',
                'shadow-[var(--shadow-md)]',
                'hover:shadow-[var(--shadow-lg)] hover:scale-[1.02]',
                'transition-all duration-300',
                'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'
              )}
              style={{ background: 'var(--gradient-hero)' }}
            >
              {submitting ? t('uploading') : t('submit')}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              {t('cancel')}
            </button>
          </div>
        </motion.form>
      )}

      {/* Materials grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="animate-pulse h-32 rounded-2xl bg-[var(--color-surface-elevated)]" aria-hidden="true" />
          ))}
        </div>
      ) : materials.length === 0 ? (
        <motion.div
          variants={itemVariants}
          className={cn(
            'flex flex-col items-center justify-center py-12 gap-4',
            'rounded-xl glass',
            'border border-dashed border-[var(--color-border)]'
          )}
        >
          <svg width="160" height="120" viewBox="0 0 160 120" fill="none" className="animate-float-slow" aria-hidden="true">
            {/* Book */}
            <rect x="45" y="20" width="70" height="80" rx="6" fill="var(--color-bg)" stroke="var(--color-primary)" strokeWidth="1.5" />
            <rect x="50" y="20" width="3" height="80" rx="1" fill="var(--color-primary)" opacity="0.3" />
            <line x1="62" y1="40" x2="100" y2="40" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
            <line x1="62" y1="52" x2="100" y2="52" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
            <line x1="62" y1="64" x2="88" y2="64" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
            {/* Upload arrow */}
            <g className="empty-state-pulse-scale" style={{ transformOrigin: '80px 15px' }}>
              <circle cx="80" cy="15" r="10" fill="var(--color-primary)" opacity="0.15" />
              <path d="M80 10L80 20M76 14L80 10L84 14" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </g>
            {/* Sparkles */}
            <path d="M130 30L132 34L136 36L132 38L130 42L128 38L124 36L128 34Z" fill="var(--color-primary)" className="empty-state-pulse-scale" opacity="0.6" />
            <path d="M25 80L26 82L28 83L26 84L25 86L24 84L22 83L24 82Z" fill="var(--color-secondary)" className="empty-state-pulse-scale" style={{ animationDelay: '1s' }} opacity="0.5" />
          </svg>
          <p className="mt-4 text-sm font-medium text-[var(--color-text)]">{t('empty')}</p>
          <p className="mt-1 text-xs text-[var(--color-muted)]">{t('empty_hint')}</p>
          <button
            onClick={() => setShowForm(true)}
            className={cn(
              'inline-flex items-center gap-2 px-6 py-3',
              'rounded-xl btn-shimmer',
              'text-sm font-semibold',
              'text-[var(--color-on-primary)]',
              'shadow-[var(--shadow-md)]',
              'hover:shadow-[var(--shadow-lg)] hover:scale-[1.02]',
              'transition-all duration-300'
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            {t('empty_cta')}
          </button>
        </motion.div>
      ) : (
        <motion.div variants={containerVariants} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {materials.map((mat) => (
            <motion.article
              key={mat.id}
              variants={itemVariants}
              className="glass card-hover rounded-2xl p-5 space-y-3 group relative overflow-hidden"
            >
              <div className="flex items-start gap-3">
                <div
                  className="flex items-center justify-center w-10 h-10 icon-orb shrink-0"
                  style={{ background: `linear-gradient(135deg, ${getSubjectColor(mat.subject)}, var(--color-secondary))` }}
                  aria-hidden="true"
                >
                  <BookIcon />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-[var(--color-text)] truncate">{mat.title}</h3>
                  <span
                    className="inline-block mt-1 px-2 py-0.5 text-xs rounded-full"
                    style={{
                      backgroundColor: `color-mix(in srgb, ${getSubjectColor(mat.subject)} 15%, transparent)`,
                      color: getSubjectColor(mat.subject),
                    }}
                  >
                    {mat.subject}
                  </span>
                </div>
              </div>

              <p className="text-xs text-[var(--color-muted)] line-clamp-2">{mat.content}</p>

              {mat.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {mat.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 text-[10px] rounded-full bg-[var(--color-surface-elevated)] text-[var(--color-muted)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <time className="block text-[10px] text-[var(--color-muted)] opacity-60">
                {new Date(mat.created_at).toLocaleDateString()}
              </time>
            </motion.article>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}

/* ===== Icons ===== */

function UploadIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )
}

function BookIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}
