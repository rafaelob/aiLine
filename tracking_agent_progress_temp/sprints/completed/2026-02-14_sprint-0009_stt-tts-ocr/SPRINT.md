# Sprint 0009 — STT / TTS / OCR

**Status:** planned | **Date:** 2026-02-14
**Goal:** Speech-to-Text (Whisper V3 Turbo via faster-whisper 1.2.1),
Text-to-Speech (ElevenLabs primary + Chatterbox Turbo MIT fallback),
image description (Opus 4.6 vision), OCR (pytesseract + surya-ocr),
voice input/output integration on tutor chat and content pages.

---

## Open-Source Models Research (2026)

### STT (Speech-to-Text)

| Model | Params | Languages | Speed | Quality | License |
|-------|--------|-----------|-------|---------|---------|
| Whisper Large V3 | 1.55B | 99+ | 1x | Best | MIT |
| Whisper Large V3 Turbo | 809M | 99+ | 6x faster | ~98% of V3 | MIT |
| Whisper Medium | 769M | 99+ | 3x | Good | MIT |

**Decision:** Whisper Large V3 Turbo (best speed/quality tradeoff for
real-time educational use). Run on backend with faster-whisper (CTranslate2
optimization) for low-latency processing. CPU inference is acceptable for
demo; GPU optional for production.

**Verified details:** faster-whisper large-v3-turbo has 809M params (vs 1.55B
for V3), achieves 6x faster inference, and retains ~98% of V3 accuracy.
Supports 99+ languages; PT-BR, EN, ES confirmed working. CTranslate2
provides the CPU optimization layer.

**Hackathon strategy:** For the hackathon demo, use the **OpenAI Whisper API**
(simplest integration, no local model download, instant setup) with
faster-whisper as the local/self-hosted fallback for production and offline
scenarios.

**OpenAI Whisper API call:**
```python
client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    language=lang,  # "pt", "en", "es"
)
```

### TTS (Text-to-Speech)

| Model | Languages | Quality | License | Latency | PT-BR |
|-------|-----------|---------|---------|---------|-------|
| Chatterbox Turbo | 23 languages | Very Good + voice cloning | MIT | ~200ms streaming | Yes |
| Kokoro | EN/JA/ZH/ES/FR/HI/IT/PT-BR | Good | Apache 2.0 | Low | Yes (3 voices) |
| OpenAudio S1-mini | Multi | Very Good + voice cloning | Apache 2.0 (code) | Low | Yes |
| MeloTTS | EN/ES/FR/CN/JP/KR | Good | MIT | Low | **No** |
| XTTS-v2 (Coqui) | 17 languages | Excellent + voice cloning | Non-commercial | 150ms | Yes |
| ElevenLabs API | 70+ | Excellent | Commercial | 75ms (Flash) | Yes |

**Decision:** Primary: ElevenLabs API (best quality, 70+ languages, Flash
v2.5 for low-latency). Fallback: **Chatterbox Turbo** (MIT license, 350M
params, 23 languages including PT-BR, streaming, emotion control, zero-shot
voice cloning). Tertiary: **Kokoro** (Apache 2.0, 82M params, CPU-friendly,
PT-BR 3 voices).

**Why not MeloTTS:** MeloTTS does NOT support PT-BR (confirmed via GitHub
issue #7). Chatterbox Turbo replaces it as the open-source fallback because
it supports all three project languages (PT-BR, EN, ES) with MIT license and
streaming (ADR-040).

**ElevenLabs verified details:** Latest models (Feb 2026): Eleven v3 (Alpha)
with 70+ languages and audio tags for emotion; Eleven Multilingual v2 for
best long-form quality; Flash v2.5 with ~75ms latency. Free tier: 10K
characters/month. Paid: Starter $5/mo (30K chars).

**Chatterbox Turbo details:** 350M params, MIT license, 23 languages including
Portuguese. Features: streaming TTS (~200ms first-chunk on GPU), zero-shot
voice cloning, emotion control via exaggeration parameter. GPU recommended
for real-time streaming; CPU usable for batch.

**Kokoro details:** 82M params (extremely lightweight), Apache 2.0, PT-BR
supported with 1 female + 2 male voices. Runs on CPU. Install:
`pip install kokoro>=0.9.4 soundfile`.

**Cost optimization:** Cache generated audio for repeated requests (same
text + voice + speed combination) to save API costs. Use a content-hash key
(SHA-256 of text + voice_id + speed + locale) mapped to cached audio bytes.
Respect ElevenLabs API rate limits and quotas; implement exponential backoff
on 429 responses. Monitor free tier character usage to avoid mid-demo
exhaustion.

**TTS fallback chain (PT-BR):**
1. **ElevenLabs** (primary, best quality, streaming)
2. **Chatterbox Turbo** (MIT, self-hosted, PT-BR + 22 other langs)
3. **Kokoro** (Apache 2.0, CPU-friendly, lightweight PT-BR)
4. **Browser SpeechSynthesis API** (zero cost, no server, immediate)

### OCR

| Tool | Languages | Quality | License |
|------|-----------|---------|---------|
| Tesseract 5.x | 100+ | Good for printed text | Apache 2.0 |
| EasyOCR | 80+ | Good for scene text | Apache 2.0 |
| Opus 4.6 Vision | Any | Excellent (contextual) | API |

**Decision:** Tesseract for structured document OCR (PDFs, worksheets).
Opus 4.6 Vision for contextual image description (diagrams, charts, photos)
and alt-text generation. The two serve complementary purposes: Tesseract
extracts raw text, Vision describes meaning.

**PDF extraction:** Use `pypdf` for text extraction from PDFs (note: PyPDF2
is deprecated and should not be used). `pypdf` handles text-layer PDFs
directly; for scanned/image-only PDFs, convert pages to images and run
Tesseract OCR.

**Image description prompt strategy:** Anthropic Messages API with vision
(Claude Opus 4.6) using a prompt tuned for educational alt-text generation.
The prompt instructs the model to describe diagrams, charts, and images in
a way that is useful for learning, not just surface-level description.

---

## Verified Library Versions

| Library | Version | Source |
|---------|---------|--------|
| faster-whisper | 1.2.1 | pypi.org/project/faster-whisper |
| CTranslate2 | 4.x | pypi.org/project/ctranslate2 |
| elevenlabs | 1.x | pypi.org/project/elevenlabs |
| chatterbox | 0.1.x | github.com/resemble-ai/chatterbox |
| kokoro | 0.9.4 | pypi.org/project/kokoro |
| pytesseract | 0.3.x | pypi.org/project/pytesseract |
| pypdf | 5.x | pypi.org/project/pypdf (NOT PyPDF2 which is deprecated) |
| Pillow | 11.x | pypi.org/project/pillow |
| anthropic | latest | pypi.org/project/anthropic |
| openai | latest | pypi.org/project/openai (for Whisper API) |

---

## Stories

### S9-001: Whisper STT Adapter (PT-BR/EN/ES)

**Description:** Implement the `STT` port using faster-whisper with the
Whisper V3 Turbo model. faster-whisper uses CTranslate2 for optimized
inference (6x faster than original Whisper, 3x less memory). The adapter
conforms to the `STT` protocol defined in `domain/ports/media.py`.

**Architecture insight:** For the hackathon, provide a dual-provider STT
implementation: (1) `OpenAIWhisperSTTAdapter` using the OpenAI Whisper API
for simplest setup (no local model, no GPU, just an API key), and
(2) `WhisperSTTAdapter` using faster-whisper for local/offline inference.
The container resolves the active adapter based on `AILINE_STT_PROVIDER`
env var (`openai` | `local`). Verified: 809M params, 99+ languages, PT-BR/
EN/ES confirmed, CTranslate2 int8 quantization for CPU.

**Files:**
- `runtime/ailine_runtime/adapters/media/whisper_stt.py` (new -- dual-provider STT adapter)

**Acceptance Criteria:**
- [ ] **OpenAI Whisper API adapter** (`OpenAIWhisperSTTAdapter`):
      - `client.audio.transcriptions.create(model="whisper-1", file=audio_file, language=lang)`
      - Simplest setup: no model download, no GPU, just `OPENAI_API_KEY`
      - Default for hackathon (`AILINE_STT_PROVIDER=openai`)
- [ ] **Local faster-whisper adapter** (`WhisperSTTAdapter`):
      - Load `whisper-large-v3-turbo` model via faster-whisper (CTranslate2
      backend)
- [ ] Transcribe audio files (WAV, WebM, MP3, OGG) with automatic language
      detection
- [ ] Explicit language support: PT-BR, EN, ES (pass `language` parameter
      to skip detection overhead)
- [ ] Return structured result: `{ text: str, language: str,
      segments: list[Segment], confidence: float }`
      where `Segment = { start: float, end: float, text: str }`
- [ ] Streaming mode: process audio chunks as they arrive via generator
      (for real-time transcription during voice input)
- [ ] GPU optional: `device="cpu"` default with `compute_type="int8"` for
      low-memory environments; `device="cuda"` with `compute_type="float16"`
      when GPU available
- [ ] Model download on first use (cached in `~/.cache/huggingface/`)
- [ ] Conforms to `STT` protocol: `async def transcribe(audio_bytes, *,
      language="pt") -> str`
- [ ] Extended method: `transcribe_detailed(audio_path, *, language=None)
      -> TranscriptionResult` for full metadata
- [ ] Temporary file handling: write audio bytes to temp file for
      faster-whisper (which requires file path), cleanup after transcription

**Implementation pattern:**

```python
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from ...domain.ports.media import STT
from ...shared.observability import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    segments: list[Segment]


class WhisperSTTAdapter:
    """STT adapter using faster-whisper (CTranslate2 backend).

    Satisfies the STT protocol from domain/ports/media.py.
    """

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            logger.info(
                "loading_whisper_model",
                model_size=self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    async def transcribe(
        self, audio_bytes: bytes, *, language: str = "pt"
    ) -> str:
        """STT protocol method: returns plain text transcription."""
        result = await self.transcribe_detailed(audio_bytes, language=language)
        return result.text

    async def transcribe_detailed(
        self,
        audio_bytes: bytes,
        *,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Extended transcription with segments and metadata."""
        model = self._ensure_model()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()

            segments_iter, info = model.transcribe(
                tmp.name,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            segments = [
                Segment(start=s.start, end=s.end, text=s.text.strip())
                for s in segments_iter
            ]

        text = " ".join(s.text for s in segments)
        return TranscriptionResult(
            text=text,
            language=info.language,
            confidence=info.language_probability,
            segments=segments,
        )
```

---

### S9-002: TTS Adapter (ElevenLabs Primary + Chatterbox Turbo Fallback)

**Description:** Implement the `TTS` port with ElevenLabs API as primary
provider and Chatterbox Turbo (MIT, 350M) as open-source fallback with PT-BR
support. Kokoro (Apache 2.0, 82M) as lightweight tertiary option. All adapters
conform to the `TTS` protocol defined in `domain/ports/media.py`. A factory
selects the active adapter based on configuration.

**Files:**
- `runtime/ailine_runtime/adapters/media/elevenlabs_tts.py` (new -- ElevenLabs adapter)
- `runtime/ailine_runtime/adapters/media/chatterbox_tts.py` (new -- Chatterbox Turbo adapter)
- `runtime/ailine_runtime/adapters/media/kokoro_tts.py` (new -- Kokoro lightweight adapter)
- `runtime/ailine_runtime/adapters/media/__init__.py` (update -- factory)

**Acceptance Criteria:**
- [ ] **ElevenLabs adapter:**
      - Stream audio from text using ElevenLabs streaming API
      - Voice selection by ID or name (default: "Rachel" for EN, "Antoni"
        for PT-BR, configurable)
      - Model: `eleven_multilingual_v2` (best multilingual quality)
      - Output format: MP3 (default) or WAV
      - Speed control via `stability` and `speed` parameters (0.5x-2.0x range)
      - Conforms to `TTS` protocol
- [ ] **Chatterbox Turbo adapter:**
      - Local inference using chatterbox library (MIT, 350M params)
      - Support PT-BR, EN, ES + 20 other languages
      - Streaming TTS: `generate_stream()` with ~200ms first-chunk latency (GPU)
      - Emotion control via `exaggeration` parameter (0.0-1.0)
      - Output format: WAV
      - Conforms to `TTS` protocol
- [ ] **Kokoro adapter (tertiary, lightweight):**
      - Local inference using kokoro library (Apache 2.0, 82M params)
      - Support PT-BR (3 voices: 1F, 2M), EN, ES
      - CPU-friendly (no GPU required)
      - Output format: WAV (24kHz)
      - Conforms to `TTS` protocol
- [ ] **Audio caching layer:**
      - Cache generated audio keyed by SHA-256(text + voice_id + speed +
        locale)
      - Return cached audio for identical requests (saves API cost)
      - Cache TTL: 24 hours (configurable)
- [ ] **ElevenLabs voice pre-selection:**
      - Pre-select warm, clear, educational-tone voices per locale for the
        demo (avoid requiring users to browse the voice library)
      - Document selected voice IDs in config
- [ ] **Rate limiting:**
      - Respect ElevenLabs API quotas
      - Exponential backoff on 429 responses
      - Per-teacher rate limits enforced server-side
- [ ] **Factory logic:**
      - If `ELEVENLABS_API_KEY` is set in config: use ElevenLabs
      - Otherwise: fall back to Chatterbox Turbo with warning log
      - Explicit override via `AILINE_TTS_PROVIDER` env var
        (`elevenlabs` | `chatterbox` | `kokoro`)
- [ ] All adapters return `bytes` (audio data)
- [ ] Support PT-BR, EN, ES voices explicitly

**ElevenLabs adapter pattern:**

```python
from elevenlabs import AsyncElevenLabs

class ElevenLabsTTSAdapter:
    """TTS adapter using ElevenLabs API.

    Satisfies the TTS protocol from domain/ports/media.py.
    """

    # Default voice IDs (ElevenLabs pre-made voices)
    VOICE_MAP = {
        "pt-BR": "pNInz6obpgDQGcFmaJgB",  # Adam (multilingual)
        "en": "21m00Tcm4TlvDq8ikWAM",      # Rachel
        "es": "29vD33N1CtxCmqQRPOHJ",      # Drew
    }

    def __init__(self, api_key: str, *, model: str = "eleven_multilingual_v2"):
        self._client = AsyncElevenLabs(api_key=api_key)
        self._model = model

    async def synthesize(
        self,
        text: str,
        *,
        locale: str = "pt-BR",
        speed: float = 1.0,
    ) -> bytes:
        voice_id = self.VOICE_MAP.get(locale, self.VOICE_MAP["en"])
        audio_iter = await self._client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=self._model,
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.75,
                "speed": speed,
            },
        )
        # Collect streamed chunks into bytes
        chunks = []
        async for chunk in audio_iter:
            chunks.append(chunk)
        return b"".join(chunks)

    async def synthesize_stream(
        self,
        text: str,
        *,
        locale: str = "pt-BR",
        speed: float = 1.0,
    ):
        """Yield audio chunks for streaming playback."""
        voice_id = self.VOICE_MAP.get(locale, self.VOICE_MAP["en"])
        audio_iter = await self._client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=self._model,
            voice_settings={"stability": 0.5, "similarity_boost": 0.75, "speed": speed},
        )
        async for chunk in audio_iter:
            yield chunk
```

---

### S9-003: Image Description (Opus 4.6 Vision)

**Description:** Use Claude Opus 4.6's vision capabilities to generate
alt-text and detailed descriptions for images in educational materials.
This enables blind and low-vision students to understand diagrams, charts,
photographs, and illustrations through screen readers or TTS.

**Architecture insight:** Uses the Anthropic Messages API with vision
capability. Opus 4.6 has the best educational image understanding among
available models. The adapter implements the `ImageDescriber(Protocol)` port
from `domain/ports/media.py`.

**Prompt template (verified):** "Describe this educational image in detail
for a screen reader. Include: main subject, text visible, diagrams/charts
explained, spatial relationships. Respond in {locale}."

**Output spec:** 200-500 character alt-text string. Detailed description
in 1-3 paragraphs for the extended method.

**Usage contexts:**
- Material ingestion: auto-generate alt-text for images in uploaded PDFs
- Accessibility exports: ensure all exported materials include image
  descriptions
- Real-time: teacher uploads an image, gets immediate alt-text suggestion

**Files:**
- `runtime/ailine_runtime/adapters/media/vision_describer.py` (new -- Vision adapter)

**Acceptance Criteria:**
- [ ] Accept image input: file path (str) or base64-encoded bytes
- [ ] Return structured description:
      ```python
      @dataclass
      class ImageDescription:
          alt_text: str           # Short (< 125 chars), suitable for alt attribute
          description: str        # Detailed (1-3 paragraphs), educational context
          content_type: str       # "diagram", "chart", "photo", "illustration", "text"
          elements: list[str]     # Key visual elements identified
          educational_notes: str  # How this image relates to learning
      ```
- [ ] Educational context: describe diagrams, charts, photos for learning
      purposes (not just "an image of..." but "a bar chart showing population
      growth in Brazil from 2000 to 2020, with the Y axis representing...")
- [ ] Accessibility-focused: alt-text suitable for screen readers (concise,
      descriptive, no "image of" prefix per WCAG guidelines)
- [ ] Multi-language output: PT-BR, EN, ES based on `locale` parameter
- [ ] Conforms to `ImageDescriber` protocol: `async def describe(image_bytes,
      *, locale="pt-BR") -> str` (returns `alt_text` for protocol
      compatibility)
- [ ] Extended method: `describe_detailed(image_bytes, *, locale) ->
      ImageDescription` for full structured output
- [ ] Token budget: limit prompt to avoid excessive cost (max 1000 output
      tokens per image)

**Implementation pattern:**

```python
import base64

from anthropic import AsyncAnthropic

from ...domain.ports.media import ImageDescriber
from ...shared.observability import get_logger

logger = get_logger(__name__)

IMAGE_DESCRIPTION_PROMPT = """Describe this image for educational purposes.
The description will be used for accessibility (screen readers, alt-text).

Provide:
1. alt_text: A concise description (< 125 characters) suitable for an HTML alt attribute.
   Do NOT start with "Image of" or "Picture of".
2. description: A detailed description (1-3 paragraphs) explaining what the image shows
   in an educational context. Describe data, relationships, and key takeaways.
3. content_type: One of: diagram, chart, photo, illustration, text, map, graph, table.
4. elements: List of key visual elements (labels, axes, data points, people, objects).
5. educational_notes: How this image relates to learning (what concept it illustrates,
   what a student should understand from it).

Respond in {locale}. Be precise and educational."""


class VisionDescriberAdapter:
    """Image description adapter using Claude Opus 4.6 Vision.

    Satisfies the ImageDescriber protocol from domain/ports/media.py.
    """

    def __init__(self, api_key: str, *, model: str = "claude-opus-4-6"):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def describe(
        self, image_bytes: bytes, *, locale: str = "pt-BR"
    ) -> str:
        """ImageDescriber protocol method: returns alt-text string."""
        result = await self.describe_detailed(image_bytes, locale=locale)
        return result.alt_text

    async def describe_detailed(
        self, image_bytes: bytes, *, locale: str = "pt-BR"
    ) -> ImageDescription:
        b64 = base64.standard_b64encode(image_bytes).decode()
        media_type = self._detect_media_type(image_bytes)

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": IMAGE_DESCRIPTION_PROMPT.format(locale=locale),
                    },
                ],
            }],
        )
        return self._parse_response(response.content[0].text)

    @staticmethod
    def _detect_media_type(image_bytes: bytes) -> str:
        if image_bytes[:8] == b"\\x89PNG\\r\\n\\x1a\\n":
            return "image/png"
        if image_bytes[:2] == b"\\xff\\xd8":
            return "image/jpeg"
        return "image/png"  # default

    def _parse_response(self, text: str) -> ImageDescription:
        # Parse structured response from LLM
        # ...
```

---

### S9-004: OCR Processor (Tesseract)

**Description:** Extract text from images and PDF pages for material
ingestion and accessibility. Tesseract handles structured printed text
(worksheets, textbook scans, handouts). Combined with S9-003 (Vision
Description) for comprehensive image understanding.

**Files:**
- `runtime/ailine_runtime/adapters/media/tesseract_ocr.py` (new -- OCR adapter)
- `runtime/ailine_runtime/adapters/media/pdf_extractor.py` (new -- PDF text extraction)

**Acceptance Criteria:**
- [ ] Process images: PNG, JPG, TIFF, BMP
- [ ] Process PDF pages: use `pypdf` for text-layer extraction first; for
      scanned/image-only PDFs, convert to images via Pillow/pdf2image, then
      OCR each page (note: PyPDF2 is deprecated -- use `pypdf` only)
- [ ] Support PT-BR, EN, ES text extraction (Tesseract language packs:
      `por`, `eng`, `spa`)
- [ ] Return structured text:
      ```python
      @dataclass
      class OCRResult:
          text: str                    # Full extracted text
          confidence: float            # Average word confidence (0-100)
          words: list[OCRWord]         # Individual words with positions
          language: str                # Detected/specified language
      @dataclass
      class OCRWord:
          text: str
          confidence: float
          bbox: tuple[int, int, int, int]  # x, y, width, height
      ```
- [ ] Quality scoring: average confidence per word; flag low-confidence
      regions (< 60%) for manual review
- [ ] Pre-processing: auto-deskew, contrast enhancement, noise reduction
      (via Pillow) before OCR for better accuracy
- [ ] Tesseract 5.x with LSTM engine (`--oem 1`)
- [ ] Docker: Tesseract installed in API container image via
      `apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-spa`

**Implementation pattern:**

```python
import pytesseract
from PIL import Image, ImageFilter, ImageOps
from io import BytesIO

class TesseractOCRAdapter:
    """OCR adapter using Tesseract 5.x.

    Extracts text from images with bounding box and confidence data.
    """

    LANG_MAP = {
        "pt-BR": "por",
        "pt": "por",
        "en": "eng",
        "es": "spa",
    }

    def __init__(self, tesseract_cmd: str | None = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    async def extract_text(
        self,
        image_bytes: bytes,
        *,
        language: str = "pt-BR",
    ) -> OCRResult:
        img = Image.open(BytesIO(image_bytes))
        img = self._preprocess(img)
        lang = self.LANG_MAP.get(language, "eng")

        # Get detailed data with confidence
        data = pytesseract.image_to_data(
            img, lang=lang, output_type=pytesseract.Output.DICT,
            config="--oem 1 --psm 6",
        )

        words = []
        for i in range(len(data["text"])):
            if data["text"][i].strip():
                words.append(OCRWord(
                    text=data["text"][i],
                    confidence=float(data["conf"][i]),
                    bbox=(data["left"][i], data["top"][i],
                          data["width"][i], data["height"][i]),
                ))

        full_text = pytesseract.image_to_string(img, lang=lang, config="--oem 1")
        avg_conf = (sum(w.confidence for w in words) / len(words)) if words else 0.0

        return OCRResult(
            text=full_text.strip(),
            confidence=avg_conf,
            words=words,
            language=language,
        )

    @staticmethod
    def _preprocess(img: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy."""
        img = ImageOps.autocontrast(img)
        img = img.convert("L")  # Grayscale
        img = img.filter(ImageFilter.SHARPEN)
        return img
```

---

### S9-005: "Read to Me" Button (Frontend)

**Description:** Add a TTS playback button to all text content throughout the
application -- plan content, tutor messages, export previews, and any long
text block. This is a core accessibility feature enabling blind, low-vision,
and dyslexic students to consume content auditorily.

**Integration flow:**
- `POST /media/synthesize` with section text -> stream audio response
- Inline audio player with play/pause/speed controls
- Keyboard shortcut: Alt+R to toggle read-aloud on focused content block

**UX enhancements:**
- **Keyboard shortcut:** Alt+R to read the current section (toggles
  play/stop on the focused content block).
- **Zero-cost fallback:** Use the browser `SpeechSynthesis` API as a no-API
  fallback when ElevenLabs is unavailable or for offline use. This provides
  immediate playback with zero server cost. Quality is lower than ElevenLabs
  but acceptable as a fallback. This is especially important for PT-BR
  fallback since MeloTTS does not support PT-BR.
- **Visual feedback:** Pulsing speaker icon while audio is actively playing;
  icon returns to static state when stopped or paused.

**Files:**
- `frontend/components/media/read-to-me-button.tsx` (new -- reusable button)
- `frontend/hooks/use-tts.ts` (new -- TTS playback hook)
- `frontend/lib/media/tts-client.ts` (new -- API client for TTS endpoint)

**Acceptance Criteria:**
- [ ] Reusable `<ReadToMeButton text={content} />` component usable anywhere
- [ ] Play / Pause / Stop controls (toggle button: speaker icon)
- [ ] Visual progress indicator: highlighted current sentence (sentence-level
      segmentation via punctuation splitting)
- [ ] Speed control: 0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x (dropdown or slider)
- [ ] Voice selection dropdown (populated from TTS adapter's available voices)
- [ ] Auto-detect content language from `next-intl` locale
- [ ] Works with all persona themes (button styling adapts)
- [ ] Audio playback via Web Audio API or `<audio>` element
- [ ] Streaming playback: start playing first chunk while remaining chunks
      download (ElevenLabs streaming)
- [ ] Keyboard shortcut: Alt+R to toggle read-aloud on focused content
- [ ] ARIA: `aria-label="Read aloud"`, `aria-pressed` for toggle state
- [ ] Mobile: 48px+ touch target, works on iOS Safari and Android Chrome

**TTS hook pattern:**

```typescript
export function useTTS() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [currentSentence, setCurrentSentence] = useState(-1);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const locale = useLocale();

  const play = async (text: string) => {
    const sentences = splitSentences(text);
    setIsPlaying(true);

    for (let i = 0; i < sentences.length; i++) {
      if (!isPlaying) break;
      setCurrentSentence(i);

      const audioBlob = await fetchTTS(sentences[i], { locale, speed });
      const url = URL.createObjectURL(audioBlob);

      await new Promise<void>((resolve) => {
        const audio = new Audio(url);
        audio.playbackRate = speed;
        audioRef.current = audio;
        audio.onended = () => {
          URL.revokeObjectURL(url);
          resolve();
        };
        audio.play();
      });
    }

    setIsPlaying(false);
    setCurrentSentence(-1);
  };

  const pause = () => {
    audioRef.current?.pause();
    setIsPaused(true);
  };

  const resume = () => {
    audioRef.current?.play();
    setIsPaused(false);
  };

  const stop = () => {
    audioRef.current?.pause();
    audioRef.current = null;
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentSentence(-1);
  };

  return { isPlaying, isPaused, speed, setSpeed, currentSentence, play, pause, resume, stop };
}
```

---

### S9-006: Voice Input for Tutor (Frontend)

**Description:** Microphone input button in the tutor chat that records
speech, sends it to the backend Whisper STT endpoint, and inserts the
transcribed text into the chat input. This enables hands-free interaction
for students with motor impairments or who prefer verbal communication.

**Integration flow:**
- MediaRecorder API -> WebM audio -> `POST /media/transcribe`
- Waveform animation while recording (AnalyserNode visualization)
- Transcribed text appears in chat input for user review before sending
  (user can edit/correct before submitting)

**Files:**
- `frontend/components/tutor/voice-input.tsx` (new -- mic button component)
- `frontend/hooks/use-stt.ts` (new -- recording + transcription hook)
- `frontend/lib/media/stt-client.ts` (new -- API client for STT endpoint)

**Acceptance Criteria:**
- [ ] Hold-to-record microphone button (48px+ touch target)
      - Press and hold: start recording
      - Release: stop recording and send to STT
      - Alternative: tap to start, tap again to stop (accessibility mode)
- [ ] Visual recording indicator: pulsing red dot + "Recording..." text
- [ ] Audio level meter during recording: real-time volume visualization
      (4-bar equalizer style using AnalyserNode)
- [ ] Send recorded audio (WebM/Opus) to backend
      `POST /media/transcribe` endpoint
- [ ] Insert transcribed text into chat input field (user can edit before
      sending)
- [ ] Language auto-detection (Whisper detects language from audio)
- [ ] Explicit language override via accessibility settings
- [ ] Loading state while transcription is processing (spinner on mic
      button)
- [ ] Error handling: microphone permission denied, network failure,
      transcription failure -- each with clear user feedback
- [ ] Works with all persona themes
- [ ] Maximum recording duration: 60 seconds (with visual countdown)
- [ ] Audio format: MediaRecorder with `audio/webm;codecs=opus` (best
      compression for speech)

**Recording hook pattern:**

```typescript
export function useSTT() {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const chunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });

      // Set up audio level monitoring
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      analyser.current = audioCtx.createAnalyser();
      source.connect(analyser.current);
      monitorAudioLevel();

      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      chunks.current = [];
      recorder.ondataavailable = (e) => chunks.current.push(e.data);
      recorder.start();
      mediaRecorder.current = recorder;
      setIsRecording(true);
      setError(null);
    } catch (err) {
      setError("Microphone access denied");
    }
  };

  const stopAndTranscribe = async (): Promise<string> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorder.current;
      if (!recorder) return reject("No recorder");

      recorder.onstop = async () => {
        setIsRecording(false);
        setIsTranscribing(true);
        try {
          const blob = new Blob(chunks.current, { type: "audio/webm" });
          const text = await sendToSTT(blob);
          resolve(text);
        } catch (err) {
          setError("Transcription failed");
          reject(err);
        } finally {
          setIsTranscribing(false);
          // Stop all tracks
          recorder.stream.getTracks().forEach((t) => t.stop());
        }
      };
      recorder.stop();
    });
  };

  return { isRecording, isTranscribing, audioLevel, error, startRecording, stopAndTranscribe };
}
```

---

### S9-007: Audio Processing API

**Description:** Backend API endpoints for STT, TTS, and image description.
These endpoints expose the media adapters (Whisper, ElevenLabs/MeloTTS,
Vision, Tesseract) as REST endpoints consumed by the frontend components.

**Files:**
- `runtime/ailine_runtime/api/routers/media.py` (new -- media router)

**Acceptance Criteria:**
- [ ] `POST /media/transcribe` -- Upload audio, return text
      - Request: `multipart/form-data` with `audio` file + optional
        `language` field
      - Response: `{ text, language, confidence, segments[] }`
      - Max file size: 25MB
      - Accepted formats: WAV, WebM, MP3, OGG, M4A
- [ ] `POST /media/synthesize` -- Send text, return audio stream
      - Request: `{ text, locale, speed, voice_id? }`
      - Response: `audio/mpeg` streaming response (chunked transfer)
      - Max text length: 5000 characters
- [ ] `POST /media/describe-image` -- Upload image, return description
      - Request: `multipart/form-data` with `image` file + optional
        `locale` field
      - Response: `{ alt_text, description, content_type, elements[],
        educational_notes }`
      - Max file size: 10MB
      - Accepted formats: PNG, JPG, GIF, WebP
- [ ] `POST /media/ocr` -- Upload image, return extracted text
      - Request: `multipart/form-data` with `image` file + optional
        `language` field
      - Response: `{ text, confidence, words[], language }`
- [ ] Streaming response for TTS (`StreamingResponse` with
      `media_type="audio/mpeg"`)
- [ ] Rate limiting per `teacher_id`: 100 STT requests/hour, 200 TTS
      requests/hour, 50 image descriptions/hour
- [ ] File validation: check MIME type, file size, reject invalid uploads
      with 422 status
- [ ] All endpoints require `teacher_id` query parameter (or from auth
      context in future)

**Router pattern:**

```python
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from ...shared.container import get_container

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
    teacher_id: str = Form(...),
):
    container = get_container()
    audio_bytes = await audio.read()

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(413, "Audio file too large (max 25MB)")

    result = await container.stt.transcribe_detailed(
        audio_bytes, language=language
    )
    return {
        "text": result.text,
        "language": result.language,
        "confidence": result.confidence,
        "segments": [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in result.segments
        ],
    }


@router.post("/synthesize")
async def synthesize(
    text: str = Form(...),
    locale: str = Form("pt-BR"),
    speed: float = Form(1.0),
    teacher_id: str = Form(...),
):
    container = get_container()

    if len(text) > 5000:
        raise HTTPException(422, "Text too long (max 5000 characters)")

    async def audio_stream():
        async for chunk in container.tts.synthesize_stream(
            text, locale=locale, speed=speed
        ):
            yield chunk

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")


@router.post("/describe-image")
async def describe_image(
    image: UploadFile = File(...),
    locale: str = Form("pt-BR"),
    teacher_id: str = Form(...),
):
    container = get_container()
    image_bytes = await image.read()

    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 10MB)")

    result = await container.image_describer.describe_detailed(
        image_bytes, locale=locale
    )
    return {
        "alt_text": result.alt_text,
        "description": result.description,
        "content_type": result.content_type,
        "elements": result.elements,
        "educational_notes": result.educational_notes,
    }
```

---

## Dependencies

**Requires:**
- Sprint 1 (clean architecture): port protocols (`STT`, `TTS`,
  `ImageDescriber` in `domain/ports/media.py`), DI container, config,
  error hierarchy
- Sprint 2 (database): Docker Compose stack (API service definition for
  adding Tesseract to image)
- Sprint 5 (frontend): Next.js scaffold, design system, i18n, persona
  themes
- Sprint 7 (tutor agents): chat panel for voice input/output integration
  points (S7-004 provides the chat UI that S9-005 and S9-006 attach to)

**Produces for:**
- Sprint 8 (sign language): sign-to-text output can be piped to TTS
- Sprint 10 (SSE streaming): media endpoints can emit progress events
  during long transcription/synthesis operations

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Whisper model size (1.5GB) increases Docker image | Medium | Download model on first use via faster-whisper's auto-download (cached in volume); do not bake into image. Document model download in `RUN_DEPLOY.md`. |
| ElevenLabs API cost at scale | Low (hackathon) | MeloTTS fallback for non-demo environments; rate limiting per teacher_id; usage dashboard planned for post-MVP |
| Real-time STT latency (>2s round-trip) | Medium | Whisper V3 Turbo is 6x faster than V3; faster-whisper with int8 quantization; VAD filter skips silence; chunked processing for streaming |
| Chatterbox Turbo is newer (2025) | Low | Kokoro as secondary fallback; both MIT/Apache 2.0; actively maintained by Resemble AI |
| Tesseract accuracy on handwritten text | Medium | Document Tesseract as "printed text only"; recommend Opus 4.6 Vision for handwritten or complex images; pre-processing (deskew, contrast) improves printed text accuracy |
| Browser microphone permission UX varies | Low | Clear permission explanation modal before requesting; fallback to text input if denied; test on Chrome, Firefox, Safari, Edge |
| Audio format compatibility across browsers | Low | MediaRecorder with WebM/Opus (best browser support); server-side format detection; accept multiple formats |

---

## Docker Changes

The API service Dockerfile (from Sprint 2) needs updates for Tesseract and
audio processing dependencies:

```dockerfile
# Add to runtime stage (before USER statement):
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-spa \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

`ffmpeg` is required by faster-whisper for audio format conversion (WebM ->
WAV). Tesseract language packs `por` and `spa` enable Portuguese and Spanish
OCR alongside the default English.

---

## Architecture: Media Adapter Port Resolution

All media adapters implement ports defined in `domain/ports/media.py`:
- `STT(Protocol)` -- speech-to-text
- `TTS(Protocol)` -- text-to-speech
- `ImageDescriber(Protocol)` -- image description / alt-text generation

The DI container resolves the concrete adapter based on environment settings:
- `AILINE_STT_PROVIDER`: `openai` (OpenAI Whisper API) | `local`
  (faster-whisper). Default: `openai` for hackathon.
- `AILINE_TTS_PROVIDER`: `elevenlabs` (ElevenLabs API) | `chatterbox`
  (Chatterbox Turbo local) | `kokoro` (Kokoro lightweight local) | `browser`
  (frontend-only SpeechSynthesis, no server adapter needed). Default:
  `elevenlabs` if API key is set, `chatterbox` otherwise.
- **PT-BR TTS fallback chain:** ElevenLabs (primary) -> Chatterbox Turbo
  (MIT, 23 langs, streaming) -> Kokoro (Apache 2.0, CPU-friendly) ->
  Browser SpeechSynthesis (zero-cost). All server-side fallbacks support
  PT-BR natively (ADR-040).

This keeps the domain layer clean and swapping providers requires only a
config change with no code modifications.

---

## Testing Plan

- **Unit tests:** Whisper adapter with pre-recorded audio samples (5s PT-BR,
  EN, ES clips); ElevenLabs adapter with mocked API client; MeloTTS adapter
  with real inference (short text); Vision describer with mock Anthropic
  client; Tesseract OCR with test images (printed PT-BR text)
- **Integration tests (Docker):** Full round-trip: upload audio ->
  `/media/transcribe` -> verify text output; upload image ->
  `/media/describe-image` -> verify structured response; Tesseract installed
  and functional in container
- **Frontend tests:** ReadToMeButton rendering and state transitions; voice
  input recording lifecycle (mock MediaRecorder); audio level visualization;
  keyboard shortcut (Alt+R) handling
- **Performance tests:** Whisper transcription latency (target: <3s for 10s
  audio on CPU); TTS synthesis latency (target: first chunk <500ms); OCR
  processing time (target: <2s per page)
- **Accessibility audit:** axe-core on all new components; screen reader
  testing with NVDA/VoiceOver for ReadToMeButton and VoiceInput; keyboard-only
  operation of all controls
