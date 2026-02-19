'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import { API_BASE, getAuthHeaders } from '@/lib/api'

interface TtsPlayerProps {
  /** Text content to synthesize. */
  text: string
  /** Optional CSS class. */
  className?: string
}

interface Voice {
  voice_id: string
  name: string
  language: string
}

type PlayerState = 'idle' | 'loading' | 'playing' | 'paused' | 'error'

const SPEED_OPTIONS = [0.5, 0.75, 1, 1.25, 1.5, 2]
const LANGUAGES = [
  { code: 'en', labelKey: 'lang_en' },
  { code: 'pt-BR', labelKey: 'lang_pt_br' },
  { code: 'es', labelKey: 'lang_es' },
] as const

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

/**
 * TTS Audio Player — synthesizes text via the backend TTS API and plays it
 * with full playback controls, speed adjustment, language/voice selection.
 * Fully keyboard-accessible with ARIA live regions for state announcements.
 */
export function TtsPlayer({ text, className }: TtsPlayerProps) {
  const t = useTranslations('tts')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const progressRef = useRef<HTMLInputElement>(null)

  const [state, setState] = useState<PlayerState>('idle')
  const [speed, setSpeed] = useState(1)
  const [language, setLanguage] = useState('en')
  const [voiceId, setVoiceId] = useState('')
  const [voices, setVoices] = useState<Voice[]>([])
  const [voicesLoading, setVoicesLoading] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')

  // Fetch voices on mount
  useEffect(() => {
    let cancelled = false
    async function fetchVoices() {
      setVoicesLoading(true)
      try {
        const res = await fetch(`${API_BASE}/media/tts/voices`, {
          headers: getAuthHeaders(),
        })
        if (!res.ok) return
        const data = (await res.json()) as { voices: Voice[] }
        if (!cancelled) {
          setVoices(data.voices ?? [])
        }
      } catch {
        // Voice loading failure is non-critical
      } finally {
        if (!cancelled) setVoicesLoading(false)
      }
    }
    fetchVoices()
    return () => { cancelled = true }
  }, [])

  // Filter voices by selected language
  const filteredVoices = voices.filter(
    (v) => v.language === language || v.language.startsWith(language),
  )

  const synthesize = useCallback(async () => {
    setState('loading')
    setErrorMsg('')
    try {
      const res = await fetch(`${API_BASE}/media/tts/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          text,
          voice_id: voiceId || undefined,
          language,
          speed,
        }),
      })
      if (!res.ok) {
        throw new Error(`TTS synthesis failed: ${res.status}`)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)

      // Clean up previous audio
      if (audioRef.current) {
        audioRef.current.pause()
        URL.revokeObjectURL(audioRef.current.src)
      }

      const audio = new Audio(url)
      audio.playbackRate = speed
      audioRef.current = audio

      audio.addEventListener('loadedmetadata', () => {
        setDuration(audio.duration)
      })
      audio.addEventListener('timeupdate', () => {
        setCurrentTime(audio.currentTime)
      })
      audio.addEventListener('ended', () => {
        setState('idle')
        setCurrentTime(0)
      })

      await audio.play()
      setState('playing')
    } catch {
      setState('error')
      setErrorMsg(t('error'))
    }
  }, [text, voiceId, language, speed, t])

  const togglePlayPause = useCallback(() => {
    if (state === 'idle' || state === 'error') {
      synthesize()
    } else if (state === 'playing' && audioRef.current) {
      audioRef.current.pause()
      setState('paused')
    } else if (state === 'paused' && audioRef.current) {
      audioRef.current.play()
      setState('playing')
    }
  }, [state, synthesize])

  const handleSpeedChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const newSpeed = parseFloat(e.target.value)
      setSpeed(newSpeed)
      if (audioRef.current) {
        audioRef.current.playbackRate = newSpeed
      }
    },
    [],
  )

  const handleLanguageChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setLanguage(e.target.value)
      setVoiceId('')
    },
    [],
  )

  const handleVoiceChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setVoiceId(e.target.value)
    },
    [],
  )

  const handleSeek = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const time = parseFloat(e.target.value)
      setCurrentTime(time)
      if (audioRef.current) {
        audioRef.current.currentTime = time
      }
    },
    [],
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        URL.revokeObjectURL(audioRef.current.src)
      }
    }
  }, [])

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <motion.div
      className={cn(
        'flex flex-col gap-3 rounded-xl p-4',
        'border border-[var(--color-border)]',
        'bg-[var(--color-surface-elevated)]',
        className,
      )}
      role="region"
      aria-label={t('player_label')}
      initial={noMotion ? undefined : { opacity: 0, y: 8 }}
      animate={noMotion ? undefined : { opacity: 1, y: 0 }}
      transition={noMotion ? undefined : { duration: 0.3 }}
    >
      {/* Play button + Progress bar */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={togglePlayPause}
          disabled={state === 'loading' || !text}
          className={cn(
            'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
            'text-white transition-all',
            'focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-[var(--color-primary)]',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            state === 'playing'
              ? 'bg-[var(--color-primary)] shadow-lg shadow-[var(--color-primary)]/25'
              : 'bg-[var(--color-primary)]/80 hover:bg-[var(--color-primary)]',
          )}
          aria-label={
            state === 'loading'
              ? t('loading')
              : state === 'playing'
                ? t('pause')
                : t('play')
          }
          aria-busy={state === 'loading'}
        >
          {state === 'loading' ? (
            <LoadingSpinner />
          ) : state === 'playing' ? (
            <PauseIcon />
          ) : (
            <PlayIcon />
          )}
        </button>

        <div className="flex flex-1 flex-col gap-1">
          {/* Progress bar */}
          <input
            ref={progressRef}
            type="range"
            min={0}
            max={duration || 0}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            disabled={state === 'idle' || state === 'loading'}
            className={cn(
              'w-full h-2 rounded-full appearance-none cursor-pointer',
              'bg-[var(--color-border)]',
              'disabled:opacity-40 disabled:cursor-not-allowed',
              '[&::-webkit-slider-thumb]:appearance-none',
              '[&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4',
              '[&::-webkit-slider-thumb]:rounded-full',
              '[&::-webkit-slider-thumb]:bg-[var(--color-primary)]',
              '[&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4',
              '[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0',
              '[&::-moz-range-thumb]:bg-[var(--color-primary)]',
            )}
            aria-label={t('progress_label', {
              current: formatTime(currentTime),
              total: formatTime(duration),
            })}
            style={{
              background: `linear-gradient(to right, var(--color-primary) ${progress}%, var(--color-border) ${progress}%)`,
            }}
          />
          {/* Time display */}
          <div className="flex justify-between text-xs text-[var(--color-muted)]">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>

      {/* Controls row: speed, language, voice */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Speed selector */}
        <div className="flex items-center gap-1.5">
          <label
            htmlFor="tts-speed"
            className="text-xs font-medium text-[var(--color-muted)]"
          >
            {t('speed_label')}
          </label>
          <select
            id="tts-speed"
            value={speed}
            onChange={handleSpeedChange}
            className={cn(
              'rounded-lg px-2 py-1 text-xs',
              'border border-[var(--color-border)]',
              'bg-[var(--color-surface)] text-[var(--color-text)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
            )}
          >
            {SPEED_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {t('speed_format', { speed: s.toString() })}
              </option>
            ))}
          </select>
        </div>

        {/* Language selector */}
        <div className="flex items-center gap-1.5">
          <label
            htmlFor="tts-language"
            className="text-xs font-medium text-[var(--color-muted)]"
          >
            {t('language_label')}
          </label>
          <select
            id="tts-language"
            value={language}
            onChange={handleLanguageChange}
            className={cn(
              'rounded-lg px-2 py-1 text-xs',
              'border border-[var(--color-border)]',
              'bg-[var(--color-surface)] text-[var(--color-text)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
            )}
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {t(lang.labelKey)}
              </option>
            ))}
          </select>
        </div>

        {/* Voice selector */}
        <div className="flex items-center gap-1.5">
          <label
            htmlFor="tts-voice"
            className="text-xs font-medium text-[var(--color-muted)]"
          >
            {t('voice_label')}
          </label>
          <select
            id="tts-voice"
            value={voiceId}
            onChange={handleVoiceChange}
            disabled={voicesLoading}
            className={cn(
              'rounded-lg px-2 py-1 text-xs',
              'border border-[var(--color-border)]',
              'bg-[var(--color-surface)] text-[var(--color-text)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              'disabled:opacity-40',
            )}
          >
            <option value="">
              {voicesLoading ? t('voice_loading') : t('voice_default')}
            </option>
            {filteredVoices.map((v) => (
              <option key={v.voice_id} value={v.voice_id}>
                {v.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error display */}
      {state === 'error' && errorMsg && (
        <p role="alert" className="text-xs text-[var(--color-error)]">
          {errorMsg}
        </p>
      )}

      {/* Screen reader live region for state changes */}
      <div aria-live="polite" className="sr-only">
        {state === 'loading' && t('loading')}
        {state === 'playing' && t('play')}
        {state === 'paused' && t('pause')}
      </div>
    </motion.div>
  )
}

/* --- Icons --- */

function PlayIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M8 5v14l11-7z" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
    </svg>
  )
}

function LoadingSpinner() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden="true"
      className="animate-spin"
    >
      <circle cx="12" cy="12" r="10" opacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" opacity="0.75" />
    </svg>
  )
}
