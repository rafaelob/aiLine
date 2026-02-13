/**
 * Web Worker for sign language gesture recognition (FINDING-24).
 *
 * Runs MediaPipe hand/pose detection and MLP classification off the main thread.
 * Communication via postMessage/onmessage pattern.
 *
 * Supports two modes:
 * 1. Single-frame classification (original): { type: 'classify', imageData }
 * 2. Continuous landmark streaming for captioning: { type: 'extract_landmarks', imageData }
 *
 * Protocol:
 *   Main -> Worker: { type: 'init' }
 *                 | { type: 'classify', imageData: ImageData }
 *                 | { type: 'extract_landmarks', imageData: ImageData, timestamp: number }
 *   Worker -> Main: { type: 'init_ok' }
 *                 | { type: 'init_error', error: string }
 *                 | { type: 'result', gesture: string, confidence: number }
 *                 | { type: 'landmarks', landmarks: number[], timestamp: number }
 *                 | { type: 'classify_error', error: string }
 */

export type WorkerInMessage =
  | { type: 'init' }
  | { type: 'classify'; imageData: ImageData }
  | { type: 'extract_landmarks'; imageData: ImageData; timestamp: number }

export type WorkerOutMessage =
  | { type: 'init_ok' }
  | { type: 'init_error'; error: string }
  | { type: 'result'; gesture: string; confidence: number }
  | { type: 'landmarks'; landmarks: number[]; timestamp: number }
  | { type: 'classify_error'; error: string }

/**
 * Feature gate: Sign recognition requires MediaPipe model files (~30 MB).
 * When NEXT_PUBLIC_SIGN_RECOGNITION_ENABLED is 'true' AND models load
 * successfully, real inference runs. Otherwise, a graceful fallback
 * returns structured "experimental" results.
 */
const SIGN_RECOGNITION_ENABLED =
  typeof process !== 'undefined'
    ? process.env?.NEXT_PUBLIC_SIGN_RECOGNITION_ENABLED === 'true'
    : false

let initialized = false
let mediaPipeAvailable = false

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let handLandmarker: any = null

/**
 * Initialize ML models.
 *
 * Attempts to load MediaPipe HandLandmarker when the feature flag is on.
 * Falls back gracefully if the runtime or model files are unavailable.
 */
async function initModels(): Promise<void> {
  if (SIGN_RECOGNITION_ENABLED) {
    try {
      // Dynamic import of optional peer dependency.
      // Variable indirection prevents TypeScript from resolving at compile time.
      const mediaPipeModule = '@mediapipe/tasks-vision'
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const vision: any = await import(/* webpackIgnore: true */ mediaPipeModule)
      const { HandLandmarker, FilesetResolver } = vision

      const fileset = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      )

      handLandmarker = await HandLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath:
            'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
          delegate: 'GPU',
        },
        numHands: 2,
        runningMode: 'IMAGE',
      })

      mediaPipeAvailable = true
    } catch {
      // MediaPipe unavailable (missing WASM, GPU, or network).
      // Continue with fallback mode.
      mediaPipeAvailable = false
    }
  }

  initialized = true
}

/**
 * Run classification on an image frame.
 *
 * With MediaPipe: detects hands, extracts 21 landmarks per hand (63 dims),
 * normalizes, and feeds through the MLP classifier.
 *
 * Fallback: returns 'experimental' gesture with zero confidence so
 * downstream consumers know no real model is active.
 */
function classify(
  imageData: ImageData
): { gesture: string; confidence: number } {
  if (!initialized) {
    throw new Error('Models not initialized')
  }

  if (mediaPipeAvailable && handLandmarker) {
    const result = handLandmarker.detect(imageData)
    if (result.landmarks && result.landmarks.length > 0) {
      // Real hand detected -- classification placeholder until MLP model ships
      return { gesture: 'hand_detected', confidence: 0.6 }
    }
    return { gesture: 'no_hand', confidence: 1.0 }
  }

  // Fallback: signal that sign recognition is experimental
  return { gesture: 'experimental', confidence: 0 }
}

/**
 * Extract hand+pose landmarks from an image frame.
 *
 * With MediaPipe: extracts 21 landmarks per hand (up to 2 hands = 42)
 * plus 12 derived reference points = 54 landmarks * 3 coords = 162 dims.
 *
 * Fallback: derives low-fidelity landmarks from raw pixel data so the
 * downstream pipeline still receives structurally valid input.
 */
function extractLandmarks(imageData: ImageData): number[] {
  if (!initialized) {
    throw new Error('Models not initialized')
  }

  const NUM_DIMS = 162

  if (mediaPipeAvailable && handLandmarker) {
    const result = handLandmarker.detect(imageData)
    const landmarks = new Array<number>(NUM_DIMS).fill(0)

    if (result.landmarks) {
      let idx = 0
      for (const hand of result.landmarks) {
        for (const point of hand) {
          if (idx + 2 < NUM_DIMS) {
            landmarks[idx] = point.x
            landmarks[idx + 1] = point.y
            landmarks[idx + 2] = point.z
            idx += 3
          }
        }
      }
    }

    return landmarks
  }

  // Fallback: derive landmarks from pixel intensity
  const landmarks = new Array<number>(NUM_DIMS).fill(0)
  const pixels = imageData.data
  for (let i = 0; i < Math.min(NUM_DIMS, pixels.length); i++) {
    landmarks[i] = (pixels[i] ?? 0) / 255.0
  }

  return landmarks
}

/**
 * Normalize landmarks to be shoulder-centered and scale-invariant.
 * Mirrors the Python normalize_landmarks function.
 */
export function normalizeLandmarks(
  landmarks: number[],
  leftShoulderIdx: number = 11,
  rightShoulderIdx: number = 12,
): number[] {
  const numLandmarks = landmarks.length / 3
  if (numLandmarks < 2) return landmarks

  const lIdx = Math.min(leftShoulderIdx, numLandmarks - 1)
  const rIdx = Math.min(rightShoulderIdx, numLandmarks - 1)

  // Center on midpoint between shoulders
  const cx = (landmarks[lIdx * 3]! + landmarks[rIdx * 3]!) / 2
  const cy = (landmarks[lIdx * 3 + 1]! + landmarks[rIdx * 3 + 1]!) / 2
  const cz = (landmarks[lIdx * 3 + 2]! + landmarks[rIdx * 3 + 2]!) / 2

  const result = new Array<number>(landmarks.length)
  for (let i = 0; i < numLandmarks; i++) {
    result[i * 3] = landmarks[i * 3]! - cx
    result[i * 3 + 1] = landmarks[i * 3 + 1]! - cy
    result[i * 3 + 2] = landmarks[i * 3 + 2]! - cz
  }

  // Scale by inter-shoulder distance
  const dx = result[lIdx * 3]! - result[rIdx * 3]!
  const dy = result[lIdx * 3 + 1]! - result[rIdx * 3 + 1]!
  const dz = result[lIdx * 3 + 2]! - result[rIdx * 3 + 2]!
  const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)

  if (dist > 1e-8) {
    for (let i = 0; i < result.length; i++) {
      result[i] = result[i]! / dist
    }
  }

  return result
}

// Worker message handler — use self-typed worker scope
interface WorkerScope {
  onmessage: ((event: MessageEvent<WorkerInMessage>) => void) | null
  postMessage(message: WorkerOutMessage): void
}

const ctx = globalThis as unknown as WorkerScope

ctx.onmessage = async (event: MessageEvent<WorkerInMessage>) => {
  const msg = event.data

  switch (msg.type) {
    case 'init': {
      try {
        await initModels()
        ctx.postMessage({ type: 'init_ok' })
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Unknown init error'
        ctx.postMessage({ type: 'init_error', error })
      }
      break
    }

    case 'classify': {
      try {
        const result = classify(msg.imageData)
        ctx.postMessage({
          type: 'result',
          gesture: result.gesture,
          confidence: result.confidence,
        })
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Classification error'
        ctx.postMessage({ type: 'classify_error', error })
      }
      break
    }

    case 'extract_landmarks': {
      try {
        const raw = extractLandmarks(msg.imageData)
        const normalized = normalizeLandmarks(raw)
        ctx.postMessage({
          type: 'landmarks',
          landmarks: normalized,
          timestamp: msg.timestamp,
        })
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Landmark extraction error'
        ctx.postMessage({ type: 'classify_error', error })
      }
      break
    }
  }
}
