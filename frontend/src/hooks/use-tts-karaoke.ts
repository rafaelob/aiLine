'use client'

import { useState, useCallback, useRef } from 'react'

interface TTSKaraokeState {
  isPlaying: boolean
  currentWordIndex: number
  speed: number
}

/**
 * Text-to-Speech hook with word-level boundary tracking for karaoke highlighting.
 * Uses the Web Speech API (SpeechSynthesis).
 */
export function useTTSKaraoke() {
  const [state, setState] = useState<TTSKaraokeState>({
    isPlaying: false,
    currentWordIndex: -1,
    speed: 1,
  })
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  const speedRef = useRef(state.speed)

  const speak = useCallback((text: string, lang: string = 'pt-BR') => {
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    utterance.rate = speedRef.current

    utterance.onboundary = (event) => {
      if (event.name === 'word') {
        const before = text.slice(0, event.charIndex)
        const wordIndex = before.split(/\s+/).filter(Boolean).length
        setState((s) => ({ ...s, currentWordIndex: wordIndex }))
      }
    }

    utterance.onend = () => {
      setState((s) => ({ ...s, isPlaying: false, currentWordIndex: -1 }))
    }

    utterance.onerror = () => {
      setState((s) => ({ ...s, isPlaying: false, currentWordIndex: -1 }))
    }

    utteranceRef.current = utterance
    setState((s) => ({ ...s, isPlaying: true, currentWordIndex: 0 }))
    window.speechSynthesis.speak(utterance)
  }, [])

  const pause = useCallback(() => {
    window.speechSynthesis.pause()
    setState((s) => ({ ...s, isPlaying: false }))
  }, [])

  const resume = useCallback(() => {
    window.speechSynthesis.resume()
    setState((s) => ({ ...s, isPlaying: true }))
  }, [])

  const stop = useCallback(() => {
    window.speechSynthesis.cancel()
    setState((s) => ({ ...s, isPlaying: false, currentWordIndex: -1 }))
  }, [])

  const setSpeed = useCallback((speed: number) => {
    speedRef.current = speed
    setState((s) => ({ ...s, speed }))
  }, [])

  return { ...state, speak, pause, resume, stop, setSpeed }
}
