# Sprint 0008 — Sign Language (Libras/ASL)

**Status:** planned | **Date:** 2026-02-13 to 2026-02-14
**Goal:** Real-time sign language recognition (Libras/ASL) via browser-side
MediaPipe + TF.js, text-to-Libras via VLibras widget, webcam capture with
visual feedback, and sign-to-text pipeline with LLM gloss correction.

---

## MVP Scope Reduction

Based on architecture review (Gemini-3-Pro-Preview + Codex consensus), the
sign language sprint scope is adjusted for hackathon feasibility:

**Tier 1 (Must-have for demo):**
- VLibras widget integration (text -> Libras 3D avatar) -- proven, gov.br CDN,
  zero training needed
- Webcam capture UI (mirrored preview, record button) -- standard browser API
- 3-4 hardcoded navigation gestures (Thumbs Up = "Yes/Confirm", Open Palm =
  "Stop/Pause", Point (index) = "Next", Wave = "Hello/Greeting")

**Tier 2 (Nice-to-have, if time permits):**
- TF.js MLP classifier on landmark sequences
- 10-20 common educational signs from WLASL dataset
- Full MediaPipe -> landmark -> gloss -> LLM pipeline

**Tier 3 (Post-hackathon — validated by research):**
- SPOTER transformer (Apache 2.0, ~10M params, pose-based) for larger vocabularies
- VLibrasBD dataset (127K PT-BR/Libras gloss pairs) for NMT training
- Real-time continuous sign language recognition
- Full vocabulary Libras-to-text translation via neural machine translation

**Risk Mitigation (key insight):**
- VLibras alone (text-to-sign) is **DEMO-WORTHY** even without gesture
  recognition working. If gesture recognition proves too difficult in the
  time window, the sprint is still a success with VLibras integration only.
- Gesture recognition is a stretch goal; show confidence scores for
  recognized gestures to demonstrate the capability even with limited
  accuracy.

---

## Architecture Decisions (from multi-model consultation)

- **Browser-side inference**: All sign language recognition runs in the browser
  using MediaPipe JS + TensorFlow.js. NO WebRTC streaming to backend. This
  eliminates latency and server load for real-time hand tracking.
- **MediaPipe Hands + Pose** (not Holistic): Holistic is deprecated in newer
  MediaPipe versions. Use `@mediapipe/tasks-vision` 0.10.32 (latest npm).
  HandLandmarker (21 landmarks per hand, each with x/y/z) + PoseLandmarker
  (33 body landmarks) gives sufficient signal for sign recognition.
  Running mode: `VIDEO` for frame-by-frame processing. GPU delegate for
  performance.
- **MVP Gesture Strategy (Tier 1 -- 3-4 gestures):** Simple distance/angle
  heuristics on raw landmarks. No ML model needed for these four gestures:
  - **Thumbs Up** = "Yes/Confirm"
  - **Open Palm** = "Stop/Pause"
  - **Point (index)** = "Next"
  - **Wave** = "Hello/Greeting"
- **Academic validation (ADR-047):** ICANN 2025 paper validated MediaPipe+MLP
  approach at 97.4% accuracy on Libras syllable recognition. This confirms
  the viability of our MVP approach for simple gesture classification.
- **Tier 2 Classifier approach**: For extended demo, use a pre-trained MLP
  classifier on MediaPipe landmarks. TF.js MLP on landmark sequences trained
  on 10-20 common educational signs from WLASL dataset. Export a TF.js model
  trained on available Libras datasets.
- **Limited vocabulary strategy**: Tier 1 = 4 gestures. Tier 2 = 10-20 signs.
  Post-MVP = ~50 signs (26 Libras alphabet + 24 common educational signs).
- **VLibras for text-to-sign**: Use the official VLibras widget (21,000+ signs,
  3 avatars: Icaro, Hosana, Guga) for converting text content to Libras
  animation. Government-backed, free, actively maintained.
- **LLM post-processing**: Use LLM to smooth recognized sign sequences (gloss)
  into coherent grammatical sentences. Libras has different grammar than
  Portuguese, so direct word-for-word mapping does not work.
- **Privacy-first**: No video data leaves the browser. All MediaPipe processing
  is local. Only recognized sign labels (text) are sent to backend for gloss
  correction.

### UI Layout Decision (Gemini-3-Pro-Preview recommendation)

**Split-panel design for sign language communication:**
- **Left panel (60%):** Main content area with `overflow-y: auto`
- **Right panel (40%):** Communication Deck, split vertically:
  - **Top half:** VLibras Avatar (output) with label "AI OUTPUT (VLibras)"
  - **Bottom half:** User Webcam (input) with label "YOUR INPUT (MediaPipe)"
- **Mobile:** Stack vertically (`flex-col`)
- `border-r` between panels
- `min-h-[300px]` per deck section
- This layout ensures the student sees both the avatar's signed output and
  their own webcam input without switching views, creating a natural
  conversational flow for sign language communication.

---

## Open-Source Sign Language Resources

| Resource | Type | Size | Language | Source |
|----------|------|------|----------|--------|
| Brazilian-Sign-Language-Alphabet | Images | 4,411 images, 15 letters | Libras | github.com/biankatpas |
| LSWH100 | Synthetic images | 144,000 images, 100 handshapes | Libras | ScienceDirect |
| LIBRAS-UFOP | RGB-D + skeleton | 56 signs, Kinect | Libras | ScienceDirect |
| sign-language-processing (GitHub org) | Tools/models | Multiple repos | Multi | github.com/sign-language-processing |
| SignGemma (Google) | Vision transformer | 10K+ hours video | ASL | Preview, not yet open |
| VLibras | Text-to-sign avatar | 21,000+ signs | Libras | vlibras.gov.br |
| MediaPipe Hands | Hand landmarks | Pre-trained | Universal | mediapipe.dev |
| WLASL | Video dataset | 2,000 words, 47K+ clips | ASL | kaggle/github |

---

## Technology Stack

| Component | Library | Version | Role |
|-----------|---------|---------|------|
| Hand tracking | @mediapipe/tasks-vision | 0.10.32 | Browser-side 21 landmarks per hand (x, y, z) |
| Pose tracking | @mediapipe/tasks-vision | 0.10.32 | 33 body landmarks for sign context |
| Classifier (Tier 2) | @tensorflow/tfjs | 4.x | MLP model for landmark-to-label inference |
| Text-to-Sign | VLibras Widget | 6.0.0 | Avatar animation (gov-backed) |
| Webcam | getUserMedia API | - | Browser native |
| Model training (Tier 2) | MediaPipe + scikit-learn + TensorFlow | - | Offline training pipeline |

---

## Stories

### S8-001: MediaPipe Landmark Extraction (Browser-Side)

**Description:** Implement real-time hand and pose landmark extraction using
MediaPipe Tasks Vision JS in the browser. This is the foundation layer -- all
sign recognition depends on accurate, fast landmark extraction from the webcam
video stream.

> **MVP Note (Tier 1 / Tier 2 split):** For MVP, the focus is on hand
> detection (present/absent) + simple gesture classification (4 gestures:
> Thumbs Up, Open Palm, Point, Wave) rather than the full 21-landmark +
> 33-pose extraction pipeline. The full pipeline is still spec'd below but
> is marked as **Tier 2**. Tier 1 only requires enough landmark data to feed
> the rule-based gesture classifier in S8-002.

**MediaPipe verified specs (from research):**
- `@mediapipe/tasks-vision` 0.10.32 (latest npm as of Feb 2026)
- `HandLandmarker`: 21 landmarks per hand (x, y, z normalized)
- `PoseLandmarker`: 33 body landmarks
- Running mode: `VIDEO` for frame-by-frame processing
- GPU delegate for performance
- Browser-side only (no server-side WebRTC needed)

**Files:**
- `frontend/lib/sign-language/mediapipe-tracker.ts` (new -- tracker class)
- `frontend/lib/sign-language/types.ts` (new -- shared types)

**Acceptance Criteria:**
- [ ] Initialize MediaPipe `HandLandmarker` + `PoseLandmarker` in browser
      using WASM backend from CDN
- [ ] Process webcam frames at 15+ FPS on mid-range hardware (i5 + integrated
      GPU or equivalent)
- [ ] Extract 21 landmarks per hand (x, y, z normalized coordinates) + 33
      pose landmarks
- [ ] Normalize landmarks relative to wrist position (translation invariance)
      and palm size (scale invariance)
- [ ] Output per frame: `LandmarkFrame { leftHand: number[63], rightHand:
      number[63], pose: number[99], timestamp: number, handsDetected: number }`
- [ ] Handles single-hand and double-hand detection gracefully (pad missing
      hand with zeros)
- [ ] Resource cleanup: dispose models on component unmount to prevent memory
      leaks
- [ ] Performance guard: if frame processing takes >100ms, reduce input
      resolution from 640x480 to 320x240

**Implementation Pattern:**

```typescript
import {
  HandLandmarker,
  PoseLandmarker,
  FilesetResolver,
} from "@mediapipe/tasks-vision";

export interface LandmarkFrame {
  leftHand: number[];   // 21 * 3 = 63 values (x, y, z)
  rightHand: number[];  // 21 * 3 = 63 values
  pose: number[];       // 33 * 3 = 99 values
  timestamp: number;
  handsDetected: number;
}

export class SignLanguageTracker {
  private handLandmarker: HandLandmarker | null = null;
  private poseLandmarker: PoseLandmarker | null = null;
  private initialized = false;

  async init(): Promise<void> {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm"
    );
    this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        delegate: "GPU",
      },
      runningMode: "VIDEO",
      numHands: 2,
      minHandDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
    this.poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "GPU",
      },
      runningMode: "VIDEO",
    });
    this.initialized = true;
  }

  processFrame(video: HTMLVideoElement, timestamp: number): LandmarkFrame {
    if (!this.initialized || !this.handLandmarker) {
      return { leftHand: new Array(63).fill(0), rightHand: new Array(63).fill(0),
               pose: new Array(99).fill(0), timestamp, handsDetected: 0 };
    }
    const handResult = this.handLandmarker.detectForVideo(video, timestamp);
    const poseResult = this.poseLandmarker?.detectForVideo(video, timestamp);
    return this.normalizeLandmarks(handResult, poseResult, timestamp);
  }

  dispose(): void {
    this.handLandmarker?.close();
    this.poseLandmarker?.close();
    this.initialized = false;
  }

  private normalizeLandmarks(
    handResult: HandLandmarkerResult,
    poseResult: PoseLandmarkerResult | undefined,
    timestamp: number,
  ): LandmarkFrame {
    // Normalize relative to wrist, flatten to number arrays
    // ...
  }
}
```

---

### S8-002: Sign Recognition Classifier (Rule-Based + TF.js)

**Description:** Implement sign recognition in two tiers. Tier 1: rule-based
gesture classifier using simple distance/angle heuristics on MediaPipe hand
landmarks for 4 navigation gestures (zero training data needed). Tier 2: train
a lightweight MLP classifier on Libras landmarks data and export to TF.js for
browser-side inference on 10-20 educational signs.

**Tier 1 -- Rule-Based Gesture Classifier (MVP, must-ship):**

The 4 MVP gestures use simple geometric heuristics on the 21 hand landmarks.
No ML model or training data required. Deterministic, implementable in <100
lines of TypeScript.

| Gesture | Mapping | Detection Heuristic |
|---------|---------|---------------------|
| Thumbs Up | "Yes/Confirm" | Fist with thumb extended upward: thumb tip y < thumb MCP y; all other fingertip y > respective MCP y |
| Open Palm | "Stop/Pause" | All fingers extended: each fingertip significantly farther from wrist than its respective MCP joint (distance check) |
| Point (index) | "Next" | Index finger extended only: index fingertip far from MCP; all other fingers curled (fingertip y > MCP y) |
| Wave | "Hello/Greeting" | Rapid horizontal oscillation of hand centroid: track x-position of wrist landmark across frames; detect 3+ direction changes within 1 second |

**Confidence scoring for gestures:**
- Each heuristic produces a confidence score (0.0-1.0) based on how strongly
  the landmark positions match the expected pattern
- Display confidence scores in the UI for all recognized gestures
- Require confidence >= 0.7 to emit a gesture recognition event

> **Tier 2 (stretch goal, if time permits):** Train a TF.js MLP classifier on
> landmark sequences for 10-20 common educational signs from WLASL dataset.
> The classifier takes normalized landmark features as input and outputs a sign
> label with confidence score. Temporal smoothing prevents flickering.

**Files:**
- `frontend/lib/sign-language/gesture-classifier.ts` (new -- Tier 1 rule-based)
- `runtime/scripts/train_sign_classifier.py` (new -- Tier 2 training script)
- `frontend/lib/sign-language/sign-classifier.ts` (new -- Tier 2 browser inference)
- `frontend/public/models/libras-classifier/model.json` (new -- Tier 2 exported model)
- `frontend/public/models/libras-classifier/group1-shard1of1.bin` (new -- Tier 2 weights)

**Acceptance Criteria (Tier 1 -- rule-based):**
- [ ] Classify 4 gestures (Thumbs Up, Open Palm, Point, Wave) from raw
      MediaPipe hand landmarks using distance/angle heuristics
- [ ] Each gesture detection returns `{ gesture: string, confidence: number }`
- [ ] Confidence threshold: predictions below 0.7 are discarded
- [ ] Temporal smoothing: require 3 consecutive frames of same prediction
      before emitting as recognized gesture (prevents flickering)
- [ ] Wave detection: track wrist x-position across frames, detect 3+
      direction changes within 1-second window
- [ ] Zero training data dependency -- works immediately with MediaPipe output
- [ ] Implementation in <100 lines of TypeScript

**Acceptance Criteria (Tier 2 -- TF.js MLP, stretch goal):**
- [ ] Training script: loads WLASL/Libras landmark data -> trains MLP
- [ ] Model architecture: Input 126 features (21 * 3 * 2 hands) -> Dense(128,
      ReLU) -> Dropout(0.3) -> Dense(64, ReLU) -> Dropout(0.3) -> Dense(N,
      Softmax) where N = number of sign classes
- [ ] Exported as TF.js LayersModel (`model.json` + `group1-shard1of1.bin`)
- [ ] Browser inference < 10ms per frame on mid-range hardware
- [ ] 10-20 common educational signs vocabulary
- [ ] Class labels stored in `labels.json` alongside model files

**Tier 1 rule-based classifier pattern:**

```typescript
// frontend/lib/sign-language/gesture-classifier.ts
import type { LandmarkFrame } from "./types";

interface GestureResult {
  gesture: string;
  confidence: number;
}

// MediaPipe hand landmark indices
const WRIST = 0;
const THUMB_TIP = 4;
const THUMB_MCP = 2;
const INDEX_TIP = 8;
const INDEX_MCP = 5;
const MIDDLE_TIP = 12;
const MIDDLE_MCP = 9;
const RING_TIP = 16;
const RING_MCP = 13;
const PINKY_TIP = 20;
const PINKY_MCP = 17;

function isFingerExtended(
  landmarks: number[],
  tipIdx: number,
  mcpIdx: number,
): boolean {
  // Compare y-coordinates (lower y = higher position in image)
  const tipY = landmarks[tipIdx * 3 + 1];
  const mcpY = landmarks[mcpIdx * 3 + 1];
  return tipY < mcpY; // tip is above MCP = extended
}

function detectThumbsUp(hand: number[]): number {
  const thumbUp = isFingerExtended(hand, THUMB_TIP, THUMB_MCP);
  const indexCurled = !isFingerExtended(hand, INDEX_TIP, INDEX_MCP);
  const middleCurled = !isFingerExtended(hand, MIDDLE_TIP, MIDDLE_MCP);
  const ringCurled = !isFingerExtended(hand, RING_TIP, RING_MCP);
  const pinkyCurled = !isFingerExtended(hand, PINKY_TIP, PINKY_MCP);
  const score = [thumbUp, indexCurled, middleCurled, ringCurled, pinkyCurled]
    .filter(Boolean).length / 5;
  return score;
}

function detectOpenPalm(hand: number[]): number {
  const fingers = [
    isFingerExtended(hand, THUMB_TIP, THUMB_MCP),
    isFingerExtended(hand, INDEX_TIP, INDEX_MCP),
    isFingerExtended(hand, MIDDLE_TIP, MIDDLE_MCP),
    isFingerExtended(hand, RING_TIP, RING_MCP),
    isFingerExtended(hand, PINKY_TIP, PINKY_MCP),
  ];
  return fingers.filter(Boolean).length / 5;
}

function detectPoint(hand: number[]): number {
  const indexExtended = isFingerExtended(hand, INDEX_TIP, INDEX_MCP);
  const middleCurled = !isFingerExtended(hand, MIDDLE_TIP, MIDDLE_MCP);
  const ringCurled = !isFingerExtended(hand, RING_TIP, RING_MCP);
  const pinkyCurled = !isFingerExtended(hand, PINKY_TIP, PINKY_MCP);
  const score = [indexExtended, middleCurled, ringCurled, pinkyCurled]
    .filter(Boolean).length / 4;
  return score;
}

export class GestureClassifier {
  private wristXHistory: number[] = [];
  private readonly WAVE_WINDOW_MS = 1000;
  private readonly WAVE_MIN_CHANGES = 3;
  private smoothingBuffer: string[] = [];
  private readonly SMOOTHING_WINDOW = 3;
  private readonly CONFIDENCE_THRESHOLD = 0.7;

  classify(frame: LandmarkFrame): GestureResult | null {
    const hand = frame.rightHand.some((v) => v !== 0)
      ? frame.rightHand
      : frame.leftHand;
    if (hand.every((v) => v === 0)) return null;

    const scores: [string, number][] = [
      ["thumbs_up", detectThumbsUp(hand)],
      ["open_palm", detectOpenPalm(hand)],
      ["point", detectPoint(hand)],
      ["wave", this.detectWave(hand, frame.timestamp)],
    ];

    const [bestGesture, bestScore] = scores.reduce(
      (best, curr) => (curr[1] > best[1] ? curr : best),
    );

    if (bestScore < this.CONFIDENCE_THRESHOLD) return null;

    // Temporal smoothing
    this.smoothingBuffer.push(bestGesture);
    if (this.smoothingBuffer.length > this.SMOOTHING_WINDOW) {
      this.smoothingBuffer.shift();
    }
    if (
      this.smoothingBuffer.length === this.SMOOTHING_WINDOW &&
      this.smoothingBuffer.every((g) => g === bestGesture)
    ) {
      this.smoothingBuffer = [];
      return { gesture: bestGesture, confidence: bestScore };
    }
    return null;
  }

  private detectWave(hand: number[], timestamp: number): number {
    const wristX = hand[WRIST * 3]; // x-coordinate of wrist
    this.wristXHistory.push(wristX);
    // Keep only last ~30 frames (1 second at 30fps)
    if (this.wristXHistory.length > 30) this.wristXHistory.shift();
    // Count direction changes
    let changes = 0;
    for (let i = 2; i < this.wristXHistory.length; i++) {
      const prev = this.wristXHistory[i - 1] - this.wristXHistory[i - 2];
      const curr = this.wristXHistory[i] - this.wristXHistory[i - 1];
      if ((prev > 0 && curr < 0) || (prev < 0 && curr > 0)) changes++;
    }
    return changes >= this.WAVE_MIN_CHANGES ? 0.8 : 0.0;
  }
}
```

**Tier 2 training script pattern:**

```python
# runtime/scripts/train_sign_classifier.py
import json
import numpy as np
import tensorflow as tf
from pathlib import Path

def build_model(num_features: int, num_classes: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(num_features,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model

def train_and_export(
    data_dir: Path,
    output_dir: Path,
    epochs: int = 50,
    batch_size: int = 32,
):
    X, y, labels = load_landmark_dataset(data_dir)
    model = build_model(X.shape[1], len(labels))
    model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.2)

    # Export for TF.js
    import tensorflowjs as tfjs
    tfjs.converters.save_keras_model(model, str(output_dir))

    # Save labels
    with open(output_dir / "labels.json", "w") as f:
        json.dump(labels, f)
```

**Tier 2 browser classifier pattern:**

```typescript
import * as tf from "@tensorflow/tfjs";

export class SignClassifier {
  private model: tf.LayersModel | null = null;
  private labels: string[] = [];
  private buffer: string[] = [];          // temporal smoothing buffer
  private readonly smoothingWindow = 3;
  private readonly confidenceThreshold = 0.7;

  async init(): Promise<void> {
    this.model = await tf.loadLayersModel("/models/libras-classifier/model.json");
    const resp = await fetch("/models/libras-classifier/labels.json");
    this.labels = await resp.json();
  }

  predict(landmarks: number[]): { label: string; confidence: number } | null {
    if (!this.model) return null;
    const input = tf.tensor2d([landmarks]);
    const output = this.model.predict(input) as tf.Tensor;
    const probs = output.dataSync();
    const maxIdx = probs.indexOf(Math.max(...probs));
    const confidence = probs[maxIdx];
    input.dispose();
    output.dispose();

    if (confidence < this.confidenceThreshold) return null;

    const label = this.labels[maxIdx];
    this.buffer.push(label);
    if (this.buffer.length > this.smoothingWindow) this.buffer.shift();

    // Require N consecutive same predictions
    if (this.buffer.length === this.smoothingWindow &&
        this.buffer.every((l) => l === label)) {
      this.buffer = []; // Reset after emit
      return { label, confidence };
    }
    return null;
  }

  dispose(): void {
    this.model?.dispose();
  }
}
```

---

### S8-003: VLibras Widget Integration

> **PRIMARY DEMO FEATURE (Tier 1).** VLibras is the cornerstone of the sign
> language demo. It is proven, free, government-backed, and has 21K+ signs
> vocabulary. Unlike the TF.js classifier (which requires training data and
> may not be ready), VLibras works out of the box with zero ML work. Focus
> demo effort and polish here first. A working VLibras integration alone
> makes the sign language sprint demo-worthy.

**Description:** Integrate the official VLibras widget for text-to-Libras
translation (avatar animation). VLibras is a Brazilian government project
that provides a 3D avatar capable of signing 21,000+ Libras signs. It renders
as an overlay widget that can translate any text content on the page.

**Exact integration code (verified via Gemini-3-Pro-Preview):**

The VLibras plugin requires two pieces: a `<Script>` load in the layout and a
specific DOM structure with `vw` attributes. This is the canonical Next.js
integration pattern:

```tsx
// In layout.tsx or global component
import Script from "next/script";

<Script
  src="https://vlibras.gov.br/app/vlibras-plugin.js"
  strategy="lazyOnload"
  onLoad={() => {
    new window.VLibras.Widget('https://vlibras.gov.br/app');
  }}
/>

// Required DOM structure (must be present in the page):
<div vw="true" className="enabled">
  <div vw-access-button="true" className="active" />
  <div vw-plugin-wrapper="true">
    <div className="vw-plugin-top-wrapper" />
  </div>
</div>
```

Note: The `vw` attribute-based DOM structure is required by VLibras to mount
its UI. The widget searches for these elements on initialization. In the
React wrapper, these must be rendered outside of strict React control (use a
portal or static HTML) to avoid hydration mismatches.

**Files:**
- `frontend/components/sign-language/vlibras-widget.tsx` (new -- React wrapper)
- `frontend/lib/sign-language/vlibras.ts` (new -- initialization + API)

**Acceptance Criteria:**
- [ ] VLibras widget loaded via Next.js `<Script>` with `strategy="lazyOnload"`
      (CDN: `https://vlibras.gov.br/app/vlibras-plugin.js`)
- [ ] Required `vw` DOM structure rendered for widget mounting
- [ ] React wrapper handles script loading lifecycle: loading -> ready -> error
- [ ] Position: bottom-right floating button (configurable via props)
- [ ] Translate any text content to Libras on demand via
      `window.VLibras.Widget.translate(text)` API
- [ ] Avatar selection: Icaro, Hosana, Guga (stored in user preferences via
      Zustand store)
- [ ] Works alongside persona themes (z-index managed to avoid overlap)
- [ ] Auto-translate plan content when Libras mode is enabled in accessibility
      settings
- [ ] Translate tutor messages automatically when Libras mode is active
      (integration point with S7-004 chat panel)
- [ ] Loading indicator while widget initializes (~3-5 seconds on first load)
- [ ] Graceful degradation: if CDN is unreachable, show error message with
      link to VLibras website
- [ ] Widget avatar renders inside the Communication Deck top half (see
      S8-004 layout) with label "AI OUTPUT (VLibras)"

**Integration pattern:**

```typescript
// frontend/lib/sign-language/vlibras.ts
declare global {
  interface Window {
    VLibras?: {
      Widget: new (config: string | VLibrasConfig) => VLibrasInstance;
    };
  }
}

interface VLibrasConfig {
  rootPath: string;
  personalization: "icaro" | "hosana" | "guga";
  opacity: number;
  position: "R" | "L" | "BR" | "BL" | "TR" | "TL";
}

interface VLibrasInstance {
  translate(text: string): void;
}

let instance: VLibrasInstance | null = null;

export async function initVLibras(
  avatar: "icaro" | "hosana" | "guga" = "icaro",
): Promise<VLibrasInstance> {
  if (instance) return instance;

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://vlibras.gov.br/app/vlibras-plugin.js";
    script.async = true;
    script.onload = () => {
      if (!window.VLibras) {
        reject(new Error("VLibras failed to initialize"));
        return;
      }
      instance = new window.VLibras.Widget({
        rootPath: "https://vlibras.gov.br/app",
        personalization: avatar,
        opacity: 1,
        position: "BR",
      });
      resolve(instance);
    };
    script.onerror = () => reject(new Error("Failed to load VLibras script"));
    document.head.appendChild(script);
  });
}

export function translateToLibras(text: string): void {
  if (instance) {
    instance.translate(text);
  }
}
```

**React wrapper pattern:**

```tsx
"use client";
import { useEffect, useState } from "react";
import Script from "next/script";
import { useAccessibilityStore } from "@/stores/accessibility";

export function VLibrasWidget() {
  const { librasEnabled, librasAvatar } = useAccessibilityStore();
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  if (!librasEnabled) return null;

  return (
    <>
      <Script
        src="https://vlibras.gov.br/app/vlibras-plugin.js"
        strategy="lazyOnload"
        onLoad={() => {
          try {
            new window.VLibras.Widget("https://vlibras.gov.br/app");
            setStatus("ready");
          } catch {
            setStatus("error");
          }
        }}
        onError={() => setStatus("error")}
      />

      {/* Required VLibras DOM structure */}
      <div vw="true" className="enabled">
        <div vw-access-button="true" className="active" />
        <div vw-plugin-wrapper="true">
          <div className="vw-plugin-top-wrapper" />
        </div>
      </div>

      {status === "loading" && (
        <div className="fixed bottom-4 right-4 p-3 bg-blue-100 rounded-lg"
             role="status" aria-label="Carregando VLibras">
          Carregando VLibras...
        </div>
      )}
      {status === "error" && (
        <div className="fixed bottom-4 right-4 p-3 bg-red-100 rounded-lg"
             role="alert">
          VLibras indisponivel.{" "}
          <a href="https://vlibras.gov.br" target="_blank" rel="noopener">
            Acesse o site
          </a>
        </div>
      )}
    </>
  );
}
```

---

### S8-004: Webcam Capture Widget

**Description:** Accessible webcam capture component with permission handling,
landmark overlay, and visual feedback for sign recognition results. This is
the primary UI for students who communicate via sign language.

**Layout Specification (Gemini-3-Pro-Preview recommendation):**

The sign language page uses a split-panel design:

```
+---------------------------+--------------------+
|                           |  AI OUTPUT         |
|   Main Content Area       |  (VLibras)         |
|   (Learning / Chat)       |  label + avatar    |
|                           |  min-h-[300px]     |
|   overflow-y: auto        +--------------------+
|   w-[60%]                 |  YOUR INPUT        |
|                           |  (MediaPipe)       |
|                           |  label + webcam    |
|                           |  min-h-[300px]     |
+---------------------------+--------------------+
         border-r              w-[40%]
```

- Left panel (60%): Main content area with `overflow-y: auto`
- Right panel (40%): Communication Deck split vertically:
  - Top half: VLibras Avatar output with label "AI OUTPUT (VLibras)"
  - Bottom half: User Webcam input with label "YOUR INPUT (MediaPipe)"
- Mobile: stack vertically using `flex-col`
- `border-r` divider between panels
- `min-h-[300px]` per deck section to ensure usable minimum size

**Webcam capture specifications (from Gemini research):**
- `getUserMedia` with `{ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" } }`
- `MediaRecorder` for recording capabilities, `Blob` handling for export
- `captureFrame()` using canvas with horizontal flip (mirror effect)
- Permission handling with explicit error states
- Cleanup on unmount (stop all tracks, release stream)

**Files:**
- `frontend/components/sign-language/webcam-capture.tsx` (new -- main component)
- `frontend/components/sign-language/communication-deck.tsx` (new -- split layout)
- `frontend/hooks/use-webcam.ts` (new -- camera management hook)
- `frontend/hooks/use-sign-recognition.ts` (new -- orchestration hook)

**Acceptance Criteria:**
- [ ] Split-panel layout: left 60% content, right 40% communication deck
- [ ] Communication deck: top half VLibras output, bottom half webcam input
- [ ] Mobile responsive: stacks vertically with `flex-col`
- [ ] `border-r` between panels, `min-h-[300px]` per deck section
- [ ] Labels: "AI OUTPUT (VLibras)" and "YOUR INPUT (MediaPipe)"
- [ ] Camera permission request with clear explanation modal ("AiLine needs
      your camera to recognize sign language. Video never leaves your device.")
- [ ] Preview window showing webcam feed with landmark overlay (hand skeleton
      drawn on canvas overlay)
- [ ] Hand detection visual feedback: green outline around detected hands,
      red when no hands detected
- [ ] Recognized sign label displayed above webcam feed (large, high-contrast
      text)
- [ ] Confidence bar: horizontal progress bar + text percentage (e.g., "85%")
- [ ] Start/Stop recognition toggle button (not recording -- processing)
- [ ] Mirror mode (selfie view) enabled by default (CSS `transform:
      scaleX(-1)` or canvas horizontal flip)
- [ ] Privacy badge: visible indicator "Processing locally" with lock icon
- [ ] Fallback message for devices without camera (`navigator.mediaDevices`
      check)
- [ ] Responsive: scales to container width, maintains 4:3 aspect ratio
- [ ] Performance indicator: FPS counter in debug mode (hidden in production)
- [ ] Resource cleanup on unmount: stop camera stream, dispose MediaPipe +
      TF.js models

**Webcam hook pattern (verified via Gemini research):**

```typescript
// frontend/hooks/use-webcam.ts
import { useRef, useState, useCallback, useEffect } from "react";

interface UseWebcamReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  hasPermission: boolean | null;
  error: string | null;
  isActive: boolean;
  start: () => Promise<void>;
  stop: () => void;
  captureFrame: () => ImageData | null;
}

export function useWebcam(): UseWebcamReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setHasPermission(true);
      setIsActive(true);
    } catch (err) {
      setHasPermission(false);
      setError(err instanceof Error ? err.message : "Camera access denied");
    }
  }, []);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  }, []);

  const captureFrame = useCallback((): ImageData | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    // Horizontal flip (mirror) for selfie view
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0); // Reset transform
    return ctx.getImageData(0, 0, canvas.width, canvas.height);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return { videoRef, canvasRef, hasPermission, error, isActive, start, stop, captureFrame };
}
```

**Communication Deck layout pattern:**

```tsx
// frontend/components/sign-language/communication-deck.tsx
"use client";

interface CommunicationDeckProps {
  contentSlot: React.ReactNode;
  vlibrasSlot: React.ReactNode;
  webcamSlot: React.ReactNode;
}

export function CommunicationDeck({
  contentSlot,
  vlibrasSlot,
  webcamSlot,
}: CommunicationDeckProps) {
  return (
    <div className="flex flex-col md:flex-row h-full">
      {/* Left panel: Main content */}
      <div className="w-full md:w-[60%] overflow-y-auto">
        {contentSlot}
      </div>

      {/* Right panel: Communication Deck */}
      <div className="w-full md:w-[40%] md:border-l flex flex-col">
        {/* Top half: VLibras Avatar output */}
        <div className="min-h-[300px] flex-1 border-b flex flex-col">
          <div className="px-3 py-2 bg-muted text-sm font-medium">
            AI OUTPUT (VLibras)
          </div>
          <div className="flex-1">{vlibrasSlot}</div>
        </div>

        {/* Bottom half: User Webcam input */}
        <div className="min-h-[300px] flex-1 flex flex-col">
          <div className="px-3 py-2 bg-muted text-sm font-medium">
            YOUR INPUT (MediaPipe)
          </div>
          <div className="flex-1">{webcamSlot}</div>
        </div>
      </div>
    </div>
  );
}
```

---

### S8-005: Sign-to-Text Pipeline (Gloss -> LLM)

**Description:** Convert recognized sign sequences into coherent text using
LLM post-processing. Libras has its own grammar (e.g., topic-comment
structure, no articles/prepositions), so raw sign sequences (gloss) need
grammatical correction to produce readable Portuguese text.

**Files:**
- `frontend/lib/sign-language/sign-to-text.ts` (new -- client-side accumulator)
- `runtime/ailine_runtime/api/routers/sign_language.py` (new -- gloss correction endpoint)

**Acceptance Criteria:**
- [ ] Client-side: accumulate recognized signs into gloss sequence (e.g.,
      "OLA PROFESSOR AJUDA ENTENDER")
- [ ] Debounce: send to backend LLM endpoint after 2s pause in signing
      (no new sign recognized for 2 seconds)
- [ ] Backend endpoint: `POST /sign-language/gloss-to-text`
      - Request: `{ gloss: "OLA PROFESSOR AJUDA ENTENDER", target_language: "pt-BR" }`
      - Response: `{ text: "Ola, professor! Preciso de ajuda para entender.", gloss_original: "..." }`
- [ ] LLM prompt for gloss correction:
      ```
      Convert this Libras gloss sequence to grammatically correct {language}.
      Libras uses topic-comment structure and omits articles/prepositions.
      Preserve the meaning faithfully. Gloss: {gloss}
      ```
- [ ] Support PT-BR, EN, ES output languages
- [ ] Display both raw gloss (smaller, gray) and corrected text (larger,
      primary color) in UI
- [ ] Gloss buffer: show real-time accumulation as signs are recognized
      (before LLM correction)
- [ ] Clear buffer button to reset accumulated signs
- [ ] Error handling: if LLM call fails, show raw gloss as fallback

**Client-side accumulator pattern:**

```typescript
export class GlossAccumulator {
  private signs: string[] = [];
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly debounceMs = 2000;
  private onFlush: (gloss: string) => void;

  constructor(onFlush: (gloss: string) => void) {
    this.onFlush = onFlush;
  }

  addSign(label: string): void {
    // Avoid consecutive duplicates (holding same sign)
    if (this.signs[this.signs.length - 1] !== label) {
      this.signs.push(label);
    }
    this.resetDebounce();
  }

  private resetDebounce(): void {
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      if (this.signs.length > 0) {
        this.onFlush(this.signs.join(" "));
        this.signs = [];
      }
    }, this.debounceMs);
  }

  getBuffer(): string {
    return this.signs.join(" ");
  }

  clear(): void {
    this.signs = [];
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
  }
}
```

---

### S8-006: Sign Language Settings & Demo

**Description:** Settings panel for sign language feature configuration and a
demo/tutorial mode where students can practice recognizing and performing
basic signs with real-time feedback.

**Files:**
- `frontend/components/sign-language/sign-settings.tsx` (new -- settings panel)
- `frontend/components/sign-language/sign-demo.tsx` (new -- tutorial/practice)
- `frontend/components/sign-language/sign-reference.tsx` (new -- vocabulary chart)

**Acceptance Criteria:**
- [ ] Enable/disable sign language features toggle (persisted in Zustand
      accessibility store)
- [ ] Choose recognition mode: Libras / ASL (determines which classifier
      model to load)
- [ ] VLibras avatar preference: Icaro / Hosana / Guga (dropdown)
- [ ] Camera selection: if multiple cameras available, dropdown to choose
- [ ] Performance mode: "Quality" (640x480, 15fps) vs "Speed" (320x240, 20fps)
- [ ] Demo page with guided sign language tutorial:
      - Show target sign image/animation
      - Student performs sign in front of webcam
      - Real-time feedback: correct (green checkmark) / try again (orange)
      - Progress tracker: 0/4 signs practiced (Tier 1: 4 MVP gestures)
      - MVP starter signs: Thumbs Up, Open Palm, Point, Wave
      - Tier 2 stretch: 10 starter signs from WLASL dataset
- [ ] Sign vocabulary reference chart:
      - Grid of supported signs (4 for Tier 1, 10-20 for Tier 2)
      - Each card: sign name + static hand position image + VLibras animation
        button
      - Search/filter by category (navigation, common, education)
- [ ] All settings respect existing persona themes and i18n

---

## Dependencies

**Requires:**
- Sprint 1 (clean architecture): port protocols (`SignRecognition` in
  `domain/ports/media.py`), DI container, config
- Sprint 5 (frontend): Next.js scaffold, design system, Zustand stores,
  i18n, accessibility preferences panel

**Produces for:**
- Sprint 7 (tutor agents): VLibras integration on tutor messages (S8-003
  auto-translate when Libras mode active)
- Sprint 9 (STT/TTS): sign-to-text output can be piped to TTS for
  audio output of signed content

---

## Risk Assessment (Expert Consultation -- Gemini-3-Pro-Preview + Codex)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| TF.js model not trained in time | High | Very High | Tier 1/2 split -- VLibras alone is demo-worthy; rule-based 4-gesture classifier as fallback (zero training data needed) |
| MediaPipe JS performance in browser | Medium | Medium | GPU delegate, 15fps+ target, test on mid-range hardware; configurable resolution fallback (640x480 -> 320x240); @mediapipe/tasks-vision 0.10.32 confirmed |
| VLibras CDN unavailable | Medium | Low | Offline fallback message with link to VLibras site; cache widget JS locally as secondary fallback |
| Gesture misrecognition | Low | Medium | Show confidence %, limit to 4 unambiguous gestures; require 3-frame temporal smoothing before emitting |
| Webcam permission denied | Medium | Medium | Clear explanation modal with privacy messaging; fallback to VLibras-only mode (text-to-sign without sign-to-text) |

---

## Risks & Mitigations (Detailed)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Limited Libras training data for Tier 2 signs | High | Tier 1 uses zero training data (rule-based); Tier 2 uses WLASL dataset; data augmentation (rotation, scaling, noise) |
| MediaPipe JS performance on low-end devices | Medium | Configurable FPS cap and resolution reduction; benchmark on target hardware (Chromebook-class); skip pose landmarks if CPU-constrained; GPU delegate default |
| VLibras widget compatibility with React/Next.js | Medium | Use Next.js `<Script>` with `strategy="lazyOnload"`; render required `vw` DOM structure; z-index management with CSS custom properties |
| TF.js model size in browser (~2-5MB) | Low | Quantize model to float16; lazy-load on first sign language feature usage; cache in service worker; only needed for Tier 2 |
| MediaPipe WASM backend CDN availability | Low | Bundle WASM files locally as fallback; pin specific version (0.10.32) to avoid breaking changes |
| Classifier accuracy with real-world lighting/backgrounds | Medium | Tier 1 rule-based approach is lighting-independent (uses relative landmark positions); Tier 2 normalizes landmarks (relative positioning reduces background dependency); confidence threshold rejects uncertain predictions |

---

## Testing Plan

- **Unit tests:** Landmark normalization (known input -> expected output);
  temporal smoothing (3-frame consistency); gloss accumulator (debounce
  behavior, duplicate suppression); rule-based gesture classifier (all 4
  gestures with known landmark inputs, confidence scoring)
- **Integration tests (backend):** Gloss-to-text endpoint with mock LLM;
  validates prompt construction and response parsing for PT-BR/EN/ES
- **Frontend tests:** Webcam component rendering with React Testing Library
  (mock getUserMedia); VLibras widget lifecycle (load/error/ready states);
  communication deck layout (split-panel responsive behavior); gesture
  classifier with pre-computed landmarks for each of the 4 MVP gestures
- **Manual testing:** Gesture recognition accuracy with 5 volunteers (target
  >80% accuracy on 4 MVP gestures); VLibras widget rendering across Chrome,
  Firefox, Edge; mobile webcam capture on Android Chrome; split-panel layout
  on mobile vs desktop
- **Accessibility audit:** axe-core on webcam component and settings panel;
  keyboard navigation through demo tutorial; screen reader compatibility
  for recognition results; "AI OUTPUT" and "YOUR INPUT" labels for screen
  readers
