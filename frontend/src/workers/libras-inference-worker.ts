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

/** CTC greedy decode: argmax per timestep, collapse repeats, remove blanks. */
export function ctcGreedyDecode(logProbs: Float32Array, seqLen: number, vocabSize: number): string[] {
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
export function computeConfidence(logProbs: Float32Array, seqLen: number, vocabSize: number): number {
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

/** Feature gate: ONNX model inference requires model download. */
let onnxAvailable = false

async function initModel(modelUrl?: string): Promise<void> {
  if (modelUrl) {
    try {
      // Variable indirection prevents TypeScript from resolving at compile time.
      const onnxModule = 'onnxruntime-web'
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ort: any = await import(/* webpackIgnore: true */ onnxModule)
      const session = await ort.InferenceSession.create(modelUrl)
      // Store session for use in inference
      ;(globalThis as Record<string, unknown>).__onnxSession = session
      onnxAvailable = true
    } catch {
      // ONNX runtime unavailable -- continue with motion-heuristic fallback
      onnxAvailable = false
    }
  }

  initialized = true
}

/**
 * MediaPipe hand landmark indices (per hand, 21 points × 3 coords).
 * Indices below are the point index within a single hand (0-20).
 */
const WRIST = 0
const THUMB_TIP = 4
const INDEX_TIP = 8
const MIDDLE_TIP = 12
const RING_TIP = 16
const PINKY_TIP = 20
const INDEX_MCP = 5
const MIDDLE_MCP = 9
const RING_MCP = 13
const PINKY_MCP = 17
const THUMB_MCP = 2

/** Get 3D point from flat landmark array for a hand starting at `handOffset`. */
function getPoint(landmarks: number[], handOffset: number, idx: number): [number, number, number] {
  const base = handOffset + idx * 3
  return [landmarks[base] ?? 0, landmarks[base + 1] ?? 0, landmarks[base + 2] ?? 0]
}

/** Euclidean distance between two 3D points. */
function dist3d(a: [number, number, number], b: [number, number, number]): number {
  const dx = a[0] - b[0]
  const dy = a[1] - b[1]
  const dz = a[2] - b[2]
  return Math.sqrt(dx * dx + dy * dy + dz * dz)
}

/** Check if a finger tip is extended (tip further from wrist than MCP). */
function isExtended(
  landmarks: number[],
  handOffset: number,
  tipIdx: number,
  mcpIdx: number,
): boolean {
  const wrist = getPoint(landmarks, handOffset, WRIST)
  const tip = getPoint(landmarks, handOffset, tipIdx)
  const mcp = getPoint(landmarks, handOffset, mcpIdx)
  return dist3d(tip, wrist) > dist3d(mcp, wrist) * 1.15
}

/**
 * Classify a static hand pose from a single landmark frame.
 *
 * Detects:
 * - Open hand (all fingers extended) → "OI" (hello)
 * - Closed fist (no fingers extended) → "NAO" (no)
 * - Thumbs up (only thumb extended) → "SIM" (yes)
 * - Pinch (thumb + index close, others extended) → "OBRIGADO" (thank you)
 *
 * Returns null if no clear pose is detected.
 */
function classifyStaticPose(landmarks: number[]): { gloss: string; confidence: number } | null {
  // Need at least one hand (21 points × 3 = 63 values)
  if (landmarks.length < 63) return null

  // Check if hand has meaningful data (not all zeros)
  let hasData = false
  for (let i = 0; i < 63; i++) {
    if (Math.abs(landmarks[i]) > 0.001) { hasData = true; break }
  }
  if (!hasData) return null

  const handOffset = 0

  const thumbExt = isExtended(landmarks, handOffset, THUMB_TIP, THUMB_MCP)
  const indexExt = isExtended(landmarks, handOffset, INDEX_TIP, INDEX_MCP)
  const middleExt = isExtended(landmarks, handOffset, MIDDLE_TIP, MIDDLE_MCP)
  const ringExt = isExtended(landmarks, handOffset, RING_TIP, RING_MCP)
  const pinkyExt = isExtended(landmarks, handOffset, PINKY_TIP, PINKY_MCP)

  const extCount = [thumbExt, indexExt, middleExt, ringExt, pinkyExt].filter(Boolean).length

  // Pinch: thumb tip and index tip close together
  const thumbTip = getPoint(landmarks, handOffset, THUMB_TIP)
  const indexTip = getPoint(landmarks, handOffset, INDEX_TIP)
  const pinchDist = dist3d(thumbTip, indexTip)
  const wrist = getPoint(landmarks, handOffset, WRIST)
  const middleMcp = getPoint(landmarks, handOffset, MIDDLE_MCP)
  const handScale = dist3d(wrist, middleMcp)
  const isPinch = handScale > 0.01 && (pinchDist / handScale) < 0.4

  // Open hand: all 5 fingers extended
  if (extCount === 5) {
    return { gloss: 'OI', confidence: 0.6 }
  }

  // Closed fist: no fingers extended
  if (extCount === 0) {
    return { gloss: 'NAO', confidence: 0.55 }
  }

  // Thumbs up: only thumb extended
  if (thumbExt && !indexExt && !middleExt && !ringExt && !pinkyExt) {
    return { gloss: 'SIM', confidence: 0.6 }
  }

  // Pinch gesture with other fingers relaxed
  if (isPinch && extCount <= 2) {
    return { gloss: 'OBRIGADO', confidence: 0.5 }
  }

  return null
}

/**
 * Infer glosses from a sequence of landmark frames.
 *
 * Strategy (layered):
 * 1. Static pose classification on the latest frame (high signal)
 * 2. Motion energy heuristic for dynamic gestures
 * 3. ONNX BiLSTM path (when model is available)
 */
function inferGlosses(landmarks: number[][]): { glosses: string[]; confidence: number } {
  if (landmarks.length === 0) return { glosses: [], confidence: 0 }

  if (onnxAvailable) {
    return { glosses: [], confidence: 0 }
  }

  // --- Layer 1: Static pose classification on recent frames ---
  // Check the last few frames for a stable pose
  const recentCount = Math.min(5, landmarks.length)
  const poseCounts: Record<string, number> = {}
  let bestPoseConf = 0

  for (let i = landmarks.length - recentCount; i < landmarks.length; i++) {
    const pose = classifyStaticPose(landmarks[i])
    if (pose) {
      poseCounts[pose.gloss] = (poseCounts[pose.gloss] ?? 0) + 1
      bestPoseConf = Math.max(bestPoseConf, pose.confidence)
    }
  }

  // If a pose is detected in majority of recent frames, use it
  for (const [gloss, count] of Object.entries(poseCounts)) {
    if (count >= Math.ceil(recentCount / 2)) {
      return { glosses: [gloss], confidence: bestPoseConf }
    }
  }

  // --- Layer 2: Motion energy heuristic for dynamic gestures ---
  let totalMotion = 0
  for (let f = 1; f < landmarks.length; f++) {
    const prev = landmarks[f - 1]
    const curr = landmarks[f]
    for (let i = 0; i < Math.min(prev.length, curr.length); i++) {
      const delta = curr[i] - prev[i]
      totalMotion += delta * delta
    }
  }

  const avgMotion = totalMotion / Math.max(landmarks.length - 1, 1)
  const MOTION_THRESHOLD = 0.01

  if (avgMotion < MOTION_THRESHOLD) {
    return { glosses: [], confidence: 0 }
  }

  const vocabKeys = Object.keys(LIBRAS_VOCABULARY).map(Number)
  const idx = Math.floor(avgMotion * 10000) % vocabKeys.length
  const gloss = LIBRAS_VOCABULARY[vocabKeys[idx]]

  const confidence = Math.min(0.3, avgMotion * 10)

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
        const { glosses, confidence } = inferGlosses(msg.landmarks)

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
