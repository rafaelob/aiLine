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

let initialized = false

/**
 * Initialize ML models. In production this would load MediaPipe + MLP weights.
 * Currently a stub that signals readiness.
 */
async function initModels(): Promise<void> {
  // TODO: Load MediaPipe HandLandmarker and MLP model weights
  // const handLandmarker = await HandLandmarker.createFromOptions(...)
  // const mlpModel = await tf.loadLayersModel(...)
  initialized = true
}

/**
 * Run classification on an image frame. In production this would:
 * 1. Run MediaPipe hand detection to get 21 landmarks (63 dims)
 * 2. Normalize landmarks
 * 3. Feed through MLP: Dense(128)->Dropout(0.3)->Dense(64)->Dense(4,softmax)
 */
function classify(
  _imageData: ImageData
): { gesture: string; confidence: number } {
  if (!initialized) {
    throw new Error('Models not initialized')
  }

  // TODO: Real inference pipeline
  return { gesture: 'unknown', confidence: 0 }
}

/**
 * Extract hand+pose landmarks from an image frame.
 *
 * In production: MediaPipe extracts 33 pose + 2*21 hand landmarks.
 * We use 54 key landmarks * 3 coords = 162 dimensions per frame.
 *
 * For MVP, returns placeholder landmarks derived from image data.
 */
function extractLandmarks(_imageData: ImageData): number[] {
  if (!initialized) {
    throw new Error('Models not initialized')
  }

  // TODO: Real MediaPipe landmark extraction
  // const poseResult = poseLandmarker.detect(imageData)
  // const handResult = handLandmarker.detect(imageData)
  // return normalizeLandmarks(combinedLandmarks)

  // Placeholder: 54 landmarks * 3 = 162 dimensions of zeros
  const numLandmarks = 162
  const landmarks = new Array<number>(numLandmarks).fill(0)

  // Add some variation based on image data for testing
  const pixels = _imageData.data
  for (let i = 0; i < Math.min(numLandmarks, pixels.length); i++) {
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
