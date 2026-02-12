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
}

/**
 * Hook to communicate with the sign language Web Worker (FINDING-24).
 * Initializes the worker on mount, provides classify() to send frames,
 * and exposes { ready, error, lastResult } state.
 */
export function useSignLanguageWorker() {
  const workerRef = useRef<Worker | null>(null)
  const [state, setState] = useState<WorkerState>({
    ready: false,
    error: null,
    lastResult: null,
  })

  useEffect(() => {
    // Create worker using the module URL pattern
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

  return {
    ready: state.ready,
    error: state.error,
    lastResult: state.lastResult,
    classify,
  } as const
}
