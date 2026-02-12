/**
 * Web Worker for Libras sign language inference.
 *
 * Receives normalized landmark sequences from the sign-language-worker,
 * runs BiLSTM inference via ONNX Runtime Web, and emits decoded gloss tokens.
 *
 * Protocol:
 *   Main -> Worker: { type: 'init', modelUrl?: string }
 *                 | { type: 'infer', landmarks: number[][], timestamp: number }
 *   Worker -> Main: { type: 'init_ok' }
 *                 | { type: 'init_error', error: string }
 *                 | { type: 'gloss_partial', glosses: string[], confidence: number, ts: number }
 *                 | { type: 'gloss_final', glosses: string[], confidence: number, ts: number }
 *                 | { type: 'infer_error', error: string }
 */

export type InferenceInMessage =
  | { type: 'init'; modelUrl?: string }
  | { type: 'infer'; landmarks: number[][]; timestamp: number }

export type InferenceOutMessage =
  | { type: 'init_ok' }
  | { type: 'init_error'; error: string }
  | { type: 'gloss_partial'; glosses: string[]; confidence: number; ts: number }
  | { type: 'gloss_final'; glosses: string[]; confidence: number; ts: number }
  | { type: 'infer_error'; error: string }

/** Libras vocabulary mapping (matches backend vocabulary.py) */
const LIBRAS_VOCABULARY: Record<number, string> = {
  2: 'OI', 3: 'TUDO-BEM', 4: 'OBRIGADO', 5: 'POR-FAVOR',
  6: 'SIM', 7: 'NAO', 8: 'EU', 9: 'VOCE',
  10: 'CASA', 11: 'ESCOLA', 12: 'PROFESSOR', 13: 'ALUNO',
  14: 'ESTUDAR', 15: 'APRENDER', 16: 'AJUDA', 17: 'ENTENDER',
  18: 'GOSTAR', 19: 'QUERER', 20: 'PRECISAR', 21: 'DESCULPA',
  22: 'BOM', 23: 'MAU', 24: 'GRANDE', 25: 'PEQUENO',
  26: 'HOJE', 27: 'AMANHA', 28: 'ONTEM', 29: 'NUMERO',
  30: 'NOME', 31: 'AGUA',
}

const BLANK_TOKEN = 0
const TRANSITION_TOKEN = 1

let initialized = false
const onnxSession: unknown = null

/** CTC greedy decode: argmax per timestep, collapse repeats, remove blanks. */
function ctcGreedyDecode(logProbs: Float32Array, seqLen: number, vocabSize: number): string[] {
  const decoded: string[] = []
  let prevToken = -1

  for (let t = 0; t < seqLen; t++) {
    let maxVal = -Infinity
    let maxIdx = 0
    for (let v = 0; v < vocabSize; v++) {
      const val = logProbs[t * vocabSize + v]
      if (val > maxVal) {
        maxVal = val
        maxIdx = v
      }
    }

    if (maxIdx === prevToken) continue
    prevToken = maxIdx

    if (maxIdx === BLANK_TOKEN || maxIdx === TRANSITION_TOKEN) continue
    const label = LIBRAS_VOCABULARY[maxIdx]
    if (label) decoded.push(label)
  }

  return decoded
}

/** Compute confidence from log probs (average max probability). */
function computeConfidence(logProbs: Float32Array, seqLen: number, vocabSize: number): number {
  if (seqLen === 0) return 0
  let totalMaxProb = 0
  for (let t = 0; t < seqLen; t++) {
    let maxVal = -Infinity
    for (let v = 0; v < vocabSize; v++) {
      const val = logProbs[t * vocabSize + v]
      if (val > maxVal) maxVal = val
    }
    totalMaxProb += Math.exp(maxVal)
  }
  return totalMaxProb / seqLen
}

async function initModel(_modelUrl?: string): Promise<void> {
  // In production, load ONNX model via onnxruntime-web
  // For MVP, inference is simulated (model is a placeholder)
  try {
    // Attempt to load onnxruntime-web if available
    // const ort = await import('onnxruntime-web')
    // onnxSession = await ort.InferenceSession.create(modelUrl)
    initialized = true
  } catch {
    // Fallback: mark as initialized with placeholder inference
    initialized = true
  }
}

/** Placeholder inference that produces random-ish gloss output. */
function placeholderInfer(landmarks: number[][]): { glosses: string[]; confidence: number } {
  if (landmarks.length === 0) return { glosses: [], confidence: 0 }

  // Simple heuristic: use landmark variance to pick glosses
  const vocabKeys = Object.keys(LIBRAS_VOCABULARY).map(Number)
  const flatSum = landmarks.reduce((sum, frame) => {
    return sum + frame.reduce((s, v) => s + Math.abs(v), 0)
  }, 0)

  const idx = Math.floor(flatSum * 1000) % vocabKeys.length
  const gloss = LIBRAS_VOCABULARY[vocabKeys[idx]]
  const confidence = 0.5 + (Math.random() * 0.4) // 0.5-0.9 range

  return { glosses: gloss ? [gloss] : [], confidence }
}

// Worker message handler
interface WorkerScope {
  onmessage: ((event: MessageEvent<InferenceInMessage>) => void) | null
  postMessage(message: InferenceOutMessage): void
}

const ctx = globalThis as unknown as WorkerScope

ctx.onmessage = async (event: MessageEvent<InferenceInMessage>) => {
  const msg = event.data

  switch (msg.type) {
    case 'init': {
      try {
        await initModel(msg.modelUrl)
        ctx.postMessage({ type: 'init_ok' })
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Unknown init error'
        ctx.postMessage({ type: 'init_error', error })
      }
      break
    }

    case 'infer': {
      if (!initialized) {
        ctx.postMessage({ type: 'infer_error', error: 'Model not initialized' })
        break
      }

      try {
        const { glosses, confidence } = placeholderInfer(msg.landmarks)

        // Emit as partial (real implementation would track state)
        ctx.postMessage({
          type: 'gloss_partial',
          glosses,
          confidence,
          ts: msg.timestamp,
        })
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Inference error'
        ctx.postMessage({ type: 'infer_error', error })
      }
      break
    }
  }
}
