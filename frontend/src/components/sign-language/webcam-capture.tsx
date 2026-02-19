'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useSignLanguageWorker } from '@/hooks/use-sign-language-worker'
import { useLibrasCaptioning } from '@/hooks/use-libras-captioning'
import type { CaptureState, WebcamErrorCode } from '@/types/sign-language'

/**
 * Webcam capture component with continuous sign language recognition (ADR-009, ADR-026).
 *
 * Unified layout:
 * - Top: live webcam feed with Start/Stop Captioning toggle
 * - Bottom: real-time caption display (glosses + translated text)
 *
 * Continuous mode uses a rAF loop at ~20fps to:
 * 1. Capture frames from video → canvas → ImageData
 * 2. Send to sign-language-worker for landmark extraction (VIDEO mode)
 * 3. Feed landmarks to libras-inference-worker via feedLandmarks()
 * 4. Inference worker → WebSocket → LLM translation → caption text
 */

interface WebcamCaptureProps {
  className?: string
}

/** Frame interval for ~20fps capture loop. */
const FRAME_INTERVAL_MS = 50

export default function WebcamCapture({ className }: WebcamCaptureProps) {
  const t = useTranslations('sign_language')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const rafRef = useRef<number>(0)
  const lastFrameTimeRef = useRef(0)
  const isCaptioningRef = useRef(false)

  const [captureState, setCaptureState] = useState<CaptureState>('idle')
  const [errorCode, setErrorCode] = useState<WebcamErrorCode | null>(null)
  const [isCaptioning, setIsCaptioning] = useState(false)
  const [captioningStatusMsg, setCaptioningStatusMsg] = useState('')

  const worker = useSignLanguageWorker()
  const captioning = useLibrasCaptioning()

  // Keep ref in sync
  useEffect(() => {
    isCaptioningRef.current = isCaptioning
  }, [isCaptioning])

  // Wire up landmark listener: when worker returns landmarks, feed to captioning
  useEffect(() => {
    worker.setLandmarkListener((landmarks) => {
      if (isCaptioningRef.current) {
        captioning.feedLandmarks(landmarks)
      }
    })
    return () => worker.setLandmarkListener(null)
  }, [worker, captioning])

  // ------- rAF capture loop -------
  // Use a ref to avoid self-reference issues with React Compiler
  const captureLoopRef = useRef<(now: number) => void>(() => {})

  const captureLoop = useCallback(
    (now: number) => {
      if (!isCaptioningRef.current) return

      // Throttle to ~20fps
      if (now - lastFrameTimeRef.current < FRAME_INTERVAL_MS) {
        rafRef.current = requestAnimationFrame(captureLoopRef.current)
        return
      }
      lastFrameTimeRef.current = now

      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 2) {
        rafRef.current = requestAnimationFrame(captureLoopRef.current)
        return
      }

      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        rafRef.current = requestAnimationFrame(captureLoopRef.current)
        return
      }

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      worker.extractLandmarks(imageData, now)

      rafRef.current = requestAnimationFrame(captureLoopRef.current)
    },
    [worker],
  )

  // Keep ref in sync with latest captureLoop
  useEffect(() => {
    captureLoopRef.current = captureLoop
  }, [captureLoop])

  // ------- Webcam lifecycle -------

  const startWebcam = useCallback(async () => {
    setCaptureState('requesting')
    setErrorCode(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setCaptureState('streaming')
    } catch (err) {
      setCaptureState('error')
      if (err instanceof DOMException) {
        if (err.name === 'NotAllowedError') {
          setErrorCode('not_allowed')
        } else if (err.name === 'NotFoundError') {
          setErrorCode('not_found')
        } else if (err.name === 'NotSupportedError') {
          setErrorCode('not_supported')
        } else {
          setErrorCode('unknown')
        }
      } else {
        setErrorCode('unknown')
      }
    }
  }, [])

  const stopWebcam = useCallback(() => {
    // Stop captioning first
    if (isCaptioningRef.current) {
      setIsCaptioning(false)
      cancelAnimationFrame(rafRef.current)
      captioning.stopCaptioning()
    }

    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop()
      }
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setCaptureState('idle')
  }, [captioning])

  const toggleCaptioning = useCallback(() => {
    if (isCaptioningRef.current) {
      // Stop captioning
      setIsCaptioning(false)
      setCaptioningStatusMsg(t('continuous_stop'))
      cancelAnimationFrame(rafRef.current)
      captioning.stopCaptioning()
    } else {
      // Start captioning
      setIsCaptioning(true)
      setCaptioningStatusMsg(t('continuous_active'))
      captioning.startCaptioning()
      lastFrameTimeRef.current = 0
      rafRef.current = requestAnimationFrame(captureLoop)
    }
  }, [captioning, captureLoop, t])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current)
      if (streamRef.current) {
        for (const track of streamRef.current.getTracks()) {
          track.stop()
        }
      }
    }
  }, [])

  // ------- Derived state -------
  const confidencePercent = Math.round(captioning.confidence * 100)

  const isActive = captureState === 'streaming' || captureState === 'capturing'
  const ringClass = isActive
    ? isCaptioning
      ? cn('ring-2 ring-[var(--color-success)] ring-offset-2 ring-offset-[var(--color-bg)]', !noMotion && 'animate-pulse')
      : 'ring-2 ring-[var(--color-primary)]/50 ring-offset-2 ring-offset-[var(--color-bg)]'
    : ''

  return (
    <div className={cn('flex flex-col gap-6', className)}>
      {/* Screen reader announcement for captioning status changes */}
      <div className="sr-only" aria-live="assertive" aria-atomic="true">
        {captioningStatusMsg}
      </div>

      {/* Webcam feed */}
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-[var(--color-text)]">
          {t('webcam')}
        </h3>
        {/* Screen reader instructions */}
        <p className="sr-only">{t('webcam_sr_instructions')}</p>

        <div
          className={cn(
            'relative aspect-video overflow-hidden rounded-[var(--radius-md)]',
            'border border-[var(--color-border)] bg-[var(--color-surface-elevated)]',
            'transition-shadow duration-300',
            ringClass,
          )}
          data-testid="webcam-container"
        >
          {captureState === 'idle' ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-[var(--color-muted)]">
                {t('webcam_off')}
              </p>
            </div>
          ) : captureState === 'error' ? (
            <div className="flex h-full items-center justify-center p-4">
              <p className="text-center text-sm text-[var(--color-error)]" role="alert">
                {errorCode === 'not_allowed'
                  ? t('error_not_allowed')
                  : errorCode === 'not_found'
                    ? t('error_not_found')
                    : errorCode === 'not_supported'
                      ? t('error_not_supported')
                      : t('error_unknown')}
              </p>
            </div>
          ) : null}

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            aria-label={t('webcam')}
            className={cn(
              'h-full w-full object-cover',
              captureState !== 'streaming' && captureState !== 'capturing' && 'hidden',
            )}
          />

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" aria-hidden="true" />

          {/* Captioning active badge */}
          {isCaptioning && (
            <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1">
              <span
                className="block h-2 w-2 rounded-full bg-[var(--color-error)]"
                style={noMotion ? undefined : { animation: 'pulse 1.5s ease-in-out infinite' }}
                aria-hidden="true"
              />
              <span className="text-xs font-medium text-white">
                {t('continuous_active')}
              </span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          {captureState === 'idle' || captureState === 'error' ? (
            <button
              type="button"
              onClick={startWebcam}
              className={cn(
                'flex-1 rounded-[var(--radius-md)] px-4 py-2.5',
                'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                'font-medium text-sm transition-colors',
                'hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2',
                'focus-visible:outline-[var(--color-primary)]',
              )}
            >
              {t('start_camera')}
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={toggleCaptioning}
                disabled={captureState !== 'streaming' && !isCaptioning}
                className={cn(
                  'flex-1 rounded-[var(--radius-md)] px-4 py-2.5',
                  'font-medium text-sm transition-colors',
                  'focus-visible:outline-2 focus-visible:outline-offset-2',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  isCaptioning
                    ? 'bg-[var(--color-error)] text-white hover:opacity-90 focus-visible:outline-[var(--color-error)]'
                    : 'bg-[var(--color-primary)] text-[var(--color-on-primary)] hover:opacity-90 focus-visible:outline-[var(--color-primary)]',
                )}
              >
                {isCaptioning ? t('continuous_stop') : t('continuous_start')}
              </button>
              <button
                type="button"
                onClick={stopWebcam}
                className={cn(
                  'rounded-[var(--radius-md)] px-4 py-2.5',
                  'border border-[var(--color-border)] text-[var(--color-text)]',
                  'font-medium text-sm transition-colors',
                  'hover:bg-[var(--color-surface-elevated)]',
                  'focus-visible:outline-2 focus-visible:outline-offset-2',
                  'focus-visible:outline-[var(--color-primary)]',
                )}
              >
                {t('stop_camera')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Caption display (integrated, always visible when streaming) */}
      {(captureState === 'streaming' || captureState === 'capturing') && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-[var(--color-muted)]">
            {t('continuous_description')}
          </p>

          <div
            className={cn(
              'relative min-h-[120px] rounded-[var(--radius-md)] p-4',
              'border border-[var(--color-border)]',
              'bg-[var(--color-surface-elevated)]',
            )}
            aria-live="polite"
            aria-atomic="false"
          >
            {/* Raw glosses line */}
            <div className="mb-2">
              <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
                {t('captioning_glosses')}
              </span>
              <div className="mt-0.5 min-h-[20px] text-sm text-[var(--color-muted)]">
                <AnimatePresence mode="wait">
                  {captioning.rawGlosses.length > 0 ? (
                    <motion.span
                      key={captioning.rawGlosses.join('-')}
                      initial={noMotion ? undefined : { opacity: 0, y: 4 }}
                      animate={noMotion ? undefined : { opacity: 0.7, y: 0 }}
                      exit={noMotion ? undefined : { opacity: 0 }}
                      transition={noMotion ? undefined : { duration: 0.2 }}
                    >
                      {captioning.rawGlosses.join(' ')}
                    </motion.span>
                  ) : (
                    <span className="opacity-40">---</span>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Translation line */}
            <div>
              <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
                {t('captioning_translation')}
              </span>
              <div className="mt-0.5 min-h-[24px] text-base">
                {captioning.committedText || captioning.draftText ? (
                  <p>
                    {captioning.committedText && (
                      <span className="text-[var(--color-text)]">{captioning.committedText}</span>
                    )}
                    {captioning.committedText && captioning.draftText && ' '}
                    {captioning.draftText && (
                      <motion.span
                        className="text-[var(--color-muted)]"
                        initial={noMotion ? undefined : { opacity: 0 }}
                        animate={noMotion ? undefined : { opacity: 0.6 }}
                        transition={noMotion ? undefined : { duration: 0.15 }}
                      >
                        {captioning.draftText}
                      </motion.span>
                    )}
                  </p>
                ) : isCaptioning ? (
                  <span className="text-sm text-[var(--color-muted)] opacity-50">
                    {t('captioning_draft')}
                  </span>
                ) : (
                  <span className="text-sm text-[var(--color-muted)] opacity-40">
                    {t('captioning_no_signs')}
                  </span>
                )}
              </div>
            </div>

            {/* Confidence bar */}
            {isCaptioning && captioning.confidence > 0 && (
              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs text-[var(--color-muted)]">
                  {t('captioning_confidence')}
                </span>
                <div
                  className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-border)]"
                  role="progressbar"
                  aria-valuenow={confidencePercent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${t('captioning_confidence')}: ${confidencePercent}%`}
                >
                  <motion.div
                    className={cn(
                      'h-full rounded-full',
                      confidencePercent >= 80
                        ? 'bg-[var(--color-success)]'
                        : confidencePercent >= 50
                          ? 'bg-[var(--color-warning)]'
                          : 'bg-[var(--color-error)]',
                    )}
                    initial={noMotion ? undefined : { width: 0 }}
                    animate={{ width: `${confidencePercent}%` }}
                    transition={noMotion ? { duration: 0 } : { duration: 0.3, ease: 'easeOut' }}
                  />
                </div>
                <span className="text-xs font-mono text-[var(--color-muted)]">
                  {confidencePercent}%
                </span>
              </div>
            )}
          </div>

          {/* Error display */}
          {captioning.error && (
            <p className="text-sm text-[var(--color-error)]" role="alert">
              {t('captioning_error')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
