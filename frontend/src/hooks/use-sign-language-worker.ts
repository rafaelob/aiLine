'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  WorkerInMessage,
  WorkerOutMessage,
} from '@/workers/sign-language-worker'

interface WorkerState {
  ready: boolean
  error: string | null
  lastResult: { gesture: string; confidence: number } | null
  lastLandmarks: { landmarks: number[]; timestamp: number } | null
}

/**
 * Hook to communicate with the sign language Web Worker (FINDING-24).
 * Initializes the worker on mount, provides classify() and extractLandmarks()
 * to send frames, and exposes { ready, error, lastResult, lastLandmarks } state.
 */
export function useSignLanguageWorker() {
  const workerRef = useRef<Worker | null>(null)
  const [state, setState] = useState<WorkerState>({
    ready: false,
    error: null,
    lastResult: null,
    lastLandmarks: null,
  })

  // Callback ref for landmark listener (avoids re-creating worker on listener change)
  const landmarkListenerRef = useRef<((landmarks: number[], timestamp: number) => void) | null>(null)

  useEffect(() => {
    const worker = new Worker(
      new URL('../workers/sign-language-worker.ts', import.meta.url),
      { type: 'module' }
    )
    workerRef.current = worker

    worker.onmessage = (event: MessageEvent<WorkerOutMessage>) => {
      const msg = event.data
      switch (msg.type) {
        case 'init_ok':
          setState((prev) => ({ ...prev, ready: true, error: null }))
          break
        case 'init_error':
          setState((prev) => ({ ...prev, ready: false, error: msg.error }))
          break
        case 'result':
          setState((prev) => ({
            ...prev,
            lastResult: { gesture: msg.gesture, confidence: msg.confidence },
          }))
          break
        case 'landmarks':
          // If a direct listener is registered, skip setState to avoid unnecessary re-renders
          if (landmarkListenerRef.current) {
            landmarkListenerRef.current(msg.landmarks, msg.timestamp)
          } else {
            setState((prev) => ({
              ...prev,
              lastLandmarks: { landmarks: msg.landmarks, timestamp: msg.timestamp },
            }))
          }
          break
        case 'classify_error':
          setState((prev) => ({ ...prev, error: msg.error }))
          break
      }
    }

    worker.onerror = (err) => {
      setState((prev) => ({ ...prev, error: err.message ?? 'Worker error' }))
    }

    // Initialize models
    const initMsg: WorkerInMessage = { type: 'init' }
    worker.postMessage(initMsg)

    return () => {
      worker.terminate()
      workerRef.current = null
    }
  }, [])

  const classify = useCallback((imageData: ImageData) => {
    if (!workerRef.current) return
    const msg: WorkerInMessage = { type: 'classify', imageData }
    workerRef.current.postMessage(msg)
  }, [])

  /** Send a frame to extract normalized landmarks (for continuous captioning). */
  const extractLandmarks = useCallback((imageData: ImageData, timestamp: number) => {
    if (!workerRef.current) return
    const msg: WorkerInMessage = { type: 'extract_landmarks', imageData, timestamp }
    workerRef.current.postMessage(msg)
  }, [])

  /** Register a callback for landmark results (avoids state-driven re-renders for high-freq data). */
  const setLandmarkListener = useCallback(
    (listener: ((landmarks: number[], timestamp: number) => void) | null) => {
      landmarkListenerRef.current = listener
    },
    [],
  )

  return {
    ready: state.ready,
    error: state.error,
    lastResult: state.lastResult,
    lastLandmarks: state.lastLandmarks,
    classify,
    extractLandmarks,
    setLandmarkListener,
  } as const
}
