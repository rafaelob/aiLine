'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useSignLanguageWorker } from '@/hooks/use-sign-language-worker'
import type {
  CaptureState,
  RecognitionResult,
  WebcamErrorCode,
} from '@/types/sign-language'

/**
 * Webcam capture component for sign language gesture recognition (ADR-009, ADR-026).
 *
 * Split-panel layout:
 * - Left: live webcam feed with a "Recognize" capture button
 * - Right: recognized gesture result with confidence score
 *
 * Uses getUserMedia to access the camera.
 * HTTPS required in production (localhost OK for dev).
 *
 * The capture button grabs a still frame from the video, converts it to a
 * Blob, and POSTs it to /sign-language/recognize.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

interface WebcamCaptureProps {
  /** Additional CSS classes for the root container. */
  className?: string
}

export function WebcamCapture({ className }: WebcamCaptureProps) {
  const t = useTranslations('sign_language')

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [captureState, setCaptureState] = useState<CaptureState>('idle')
  const [errorCode, setErrorCode] = useState<WebcamErrorCode | null>(null)
  const [result, setResult] = useState<RecognitionResult | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)

  // Web Worker for off-main-thread ML inference (FINDING-24)
  const worker = useSignLanguageWorker()

  // Update result when worker produces a classification
  useEffect(() => {
    if (worker.lastResult) {
      setResult({
        gesture: worker.lastResult.gesture,
        confidence: worker.lastResult.confidence,
        landmarks: [],
        model: 'mediapipe-mlp-worker',
      })
      setIsRecognizing(false)
      setCaptureState('streaming')
    }
  }, [worker.lastResult])

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
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        for (const track of streamRef.current.getTracks()) {
          track.stop()
        }
      }
    }
  }, [])

  // ------- Capture & recognize -------

  const captureAndRecognize = useCallback(async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || captureState !== 'streaming') return

    setIsRecognizing(true)
    setCaptureState('capturing')

    // Draw current video frame to canvas
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      setIsRecognizing(false)
      setCaptureState('streaming')
      return
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert to Blob and POST to API
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setIsRecognizing(false)
        setCaptureState('streaming')
        return
      }

      try {
        const formData = new FormData()
        formData.append('file', blob, 'capture.png')

        const response = await fetch(`${API_BASE}/sign-language/recognize`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data: RecognitionResult = await response.json()
        setResult(data)
      } catch {
        setResult(null)
      } finally {
        setIsRecognizing(false)
        setCaptureState('streaming')
      }
    }, 'image/png')
  }, [captureState])

  // ------- Render helpers -------

  const confidencePercent = result ? Math.round(result.confidence * 100) : 0
  const confidenceColor =
    confidencePercent >= 80
      ? 'text-[var(--color-success)]'
      : confidencePercent >= 50
        ? 'text-[var(--color-warning)]'
        : 'text-[var(--color-error)]'

  return (
    <div className={cn('grid gap-6 md:grid-cols-2', className)}>
      {/* Left panel: webcam feed */}
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-[var(--color-text)]">
          {t('webcam')}
        </h3>

        <div
          className={cn(
            'relative aspect-video overflow-hidden rounded-[var(--radius-md)]',
            'border border-[var(--color-border)] bg-[var(--color-surface-elevated)]'
          )}
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
            className={cn(
              'h-full w-full object-cover',
              captureState !== 'streaming' && captureState !== 'capturing' && 'hidden'
            )}
          />

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" aria-hidden="true" />
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
                'focus-visible:outline-[var(--color-primary)]'
              )}
            >
              {t('start_camera')}
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={captureAndRecognize}
                disabled={isRecognizing || captureState !== 'streaming'}
                aria-busy={isRecognizing}
                className={cn(
                  'flex-1 rounded-[var(--radius-md)] px-4 py-2.5',
                  'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                  'font-medium text-sm transition-colors',
                  'hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2',
                  'focus-visible:outline-[var(--color-primary)]',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {isRecognizing ? t('recognizing') : t('recognize')}
              </button>
              <button
                type="button"
                onClick={stopWebcam}
                className={cn(
                  'rounded-[var(--radius-md)] px-4 py-2.5',
                  'border border-[var(--color-border)] text-[var(--color-text)]',
                  'font-medium text-sm transition-colors',
                  'hover:bg-[var(--color-surface-elevated)]'
                )}
              >
                {t('stop_camera')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Right panel: recognition result */}
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-[var(--color-text)]">
          {t('result')}
        </h3>

        <div
          className={cn(
            'flex flex-1 flex-col items-center justify-center gap-4',
            'rounded-[var(--radius-md)] border border-[var(--color-border)]',
            'bg-[var(--color-surface-elevated)] p-6'
          )}
        >
          {result ? (
            <>
              <p
                className="text-4xl font-bold text-[var(--color-text)]"
                aria-live="polite"
              >
                {result.gesture === 'unknown'
                  ? t('gesture_unknown')
                  : result.gesture.charAt(0).toUpperCase() + result.gesture.slice(1)}
              </p>
              <p className={cn('text-2xl font-semibold', confidenceColor)}>
                {confidencePercent}%
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {t('model')}: {result.model}
              </p>
            </>
          ) : (
            <p className="text-sm text-[var(--color-muted)]">
              {t('no_result')}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
