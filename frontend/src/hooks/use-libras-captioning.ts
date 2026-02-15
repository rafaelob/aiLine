'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  InferenceOutMessage,
} from '@/workers/libras-inference-worker'
import { API_BASE } from '@/lib/api'
const WS_BASE = API_BASE.replace(/^http/, 'ws')

export interface CaptioningState {
  /** Whether captioning is actively recording */
  isRecording: boolean
  /** Raw detected glosses */
  rawGlosses: string[]
  /** Draft translation text (in progress) */
  draftText: string
  /** Final committed translation text */
  committedText: string
  /** Current confidence score (0-1) */
  confidence: number
  /** WebSocket connection status */
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  /** Error message if any */
  error: string | null
}

/**
 * Hook for real-time Libras captioning.
 *
 * Connects a libras-inference-worker for local gloss detection
 * and a WebSocket to the backend for LLM-based translation.
 *
 * Flow:
 *   Camera frames -> sign-language-worker (landmarks)
 *   -> libras-inference-worker (gloss detection)
 *   -> WebSocket (LLM translation)
 *   -> caption text displayed
 */
export function useLibrasCaptioning() {
  const [state, setState] = useState<CaptioningState>({
    isRecording: false,
    rawGlosses: [],
    draftText: '',
    committedText: '',
    confidence: 0,
    connectionStatus: 'disconnected',
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const inferenceWorkerRef = useRef<Worker | null>(null)
  const frameBufferRef = useRef<number[][]>([])
  const isRecordingRef = useRef(false)

  // Keep ref in sync with state
  useEffect(() => {
    isRecordingRef.current = state.isRecording
  }, [state.isRecording])

  // Initialize inference worker
  useEffect(() => {
    const worker = new Worker(
      new URL('../workers/libras-inference-worker.ts', import.meta.url),
      { type: 'module' }
    )
    inferenceWorkerRef.current = worker

    worker.onmessage = (event: MessageEvent<InferenceOutMessage>) => {
      const msg = event.data

      switch (msg.type) {
        case 'init_ok':
          break

        case 'gloss_partial': {
          setState(prev => ({
            ...prev,
            rawGlosses: msg.glosses,
            confidence: msg.confidence,
          }))
          // Send to WebSocket if connected
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'gloss_partial',
              glosses: msg.glosses,
              confidence: msg.confidence,
              ts: msg.ts,
            }))
          }
          break
        }

        case 'gloss_final': {
          setState(prev => ({
            ...prev,
            rawGlosses: msg.glosses,
            confidence: msg.confidence,
          }))
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'gloss_final',
              glosses: msg.glosses,
              confidence: msg.confidence,
              ts: msg.ts,
            }))
          }
          break
        }

        case 'init_error':
          setState(prev => ({ ...prev, error: msg.error }))
          break

        case 'infer_error':
          setState(prev => ({ ...prev, error: msg.error }))
          break
      }
    }

    worker.postMessage({ type: 'init' })

    return () => {
      worker.terminate()
      inferenceWorkerRef.current = null
    }
  }, [])

  /** Connect WebSocket to backend for LLM translation */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setState(prev => ({ ...prev, connectionStatus: 'connecting' }))

    const ws = new WebSocket(`${WS_BASE}/sign-language/ws/libras-caption`)
    wsRef.current = ws

    ws.onopen = () => {
      setState(prev => ({ ...prev, connectionStatus: 'connected', error: null }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string)

        if (msg.type === 'caption_draft_delta') {
          setState(prev => ({
            ...prev,
            draftText: msg.text ?? '',
          }))
        } else if (msg.type === 'caption_final_delta') {
          setState(prev => ({
            ...prev,
            committedText: msg.full_text ?? prev.committedText + ' ' + (msg.text ?? ''),
            draftText: '',
          }))
        } else if (msg.type === 'error') {
          setState(prev => ({ ...prev, error: msg.detail }))
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onerror = () => {
      setState(prev => ({ ...prev, connectionStatus: 'error', error: 'WebSocket error' }))
    }

    ws.onclose = () => {
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
      wsRef.current = null
    }
  }, [])

  /** Disconnect WebSocket */
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
  }, [])

  /** Feed a landmark frame to the inference pipeline */
  const feedLandmarks = useCallback((landmarks: number[]) => {
    if (!isRecordingRef.current) return

    frameBufferRef.current.push(landmarks)

    // Keep rolling window of 60 frames (~2 seconds at 30fps)
    const maxFrames = 60
    if (frameBufferRef.current.length > maxFrames) {
      frameBufferRef.current = frameBufferRef.current.slice(-maxFrames)
    }

    // Send to inference every 10 frames
    if (frameBufferRef.current.length % 10 === 0) {
      inferenceWorkerRef.current?.postMessage({
        type: 'infer',
        landmarks: frameBufferRef.current,
        timestamp: Date.now(),
      })
    }
  }, [])

  /** Start captioning: connect WS and begin recording */
  const startCaptioning = useCallback(() => {
    connectWebSocket()
    frameBufferRef.current = []
    setState(prev => ({
      ...prev,
      isRecording: true,
      rawGlosses: [],
      draftText: '',
      committedText: '',
      confidence: 0,
      error: null,
    }))
  }, [connectWebSocket])

  /** Stop captioning: disconnect WS and stop recording */
  const stopCaptioning = useCallback(() => {
    setState(prev => ({ ...prev, isRecording: false }))
    frameBufferRef.current = []
    disconnectWebSocket()
  }, [disconnectWebSocket])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return {
    ...state,
    startCaptioning,
    stopCaptioning,
    feedLandmarks,
  } as const
}
