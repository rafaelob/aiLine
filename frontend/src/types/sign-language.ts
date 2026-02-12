/**
 * Sign language types for webcam capture, gesture recognition,
 * and VLibras integration (ADR-009, ADR-026).
 */

/** A single recognized gesture from the server. */
export interface RecognitionResult {
  gesture: string
  confidence: number
  landmarks: unknown[]
  model: string
  note?: string
}

/** A supported gesture descriptor with multilingual names. */
export interface GestureInfo {
  id: string
  name_pt: string
  name_en: string
  name_es: string
}

/** Response from GET /sign-language/gestures. */
export interface GestureListResponse {
  gestures: GestureInfo[]
  model: string
  note: string
}

/** Webcam capture state. */
export type CaptureState = 'idle' | 'requesting' | 'streaming' | 'capturing' | 'error'

/** Error codes for webcam access failures. */
export type WebcamErrorCode =
  | 'not_allowed'
  | 'not_found'
  | 'not_supported'
  | 'unknown'
