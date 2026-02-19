# Sprint 25 Research Report — TTS, Braille, Skills Interfaces

## 1. ElevenLabs TTS API

### 1.1 Available Models (from live API query)

| Model ID | Name | Languages | Best For |
|----------|------|-----------|----------|
| `eleven_v3` | Eleven v3 | 74 languages (incl. PT, ES, EN) | **Newest, highest quality** |
| `eleven_v3_dpo_20260217` | Eleven v3 (DPO) | 74 languages | Latest DPO-tuned variant |
| `eleven_multilingual_v2` | Multilingual v2 | 29 languages (incl. PT, ES, EN) | **Current default in our adapter** |
| `eleven_flash_v2_5` | Flash v2.5 | 32 languages | Ultra-low latency |
| `eleven_turbo_v2_5` | Turbo v2.5 | 32 languages | Balanced quality/speed |
| `eleven_turbo_v2` | Turbo v2 | English only | English-only fast |
| `eleven_flash_v2` | Flash v2 | English only | English-only ultra-fast |
| `eleven_monolingual_v1` | English v1 | English only | Legacy |

**Recommendation:** Upgrade default from `eleven_multilingual_v2` to `eleven_v3` (74 languages vs 29, newer model). Keep `eleven_flash_v2_5` as low-latency fallback.

### 1.2 API Endpoints

**Non-streaming:** `POST /v1/text-to-speech/{voice_id}`
- Request body: `{ text, model_id, voice_settings: { stability, similarity_boost }, language_code }`
- Returns: raw audio bytes (mpeg)
- Auth: `xi-api-key` header

**Streaming:** `POST /v1/text-to-speech/{voice_id}/stream`
- Same body + `optimize_streaming_latency` (0-4)
- Returns: chunked audio stream
- Ideal for long texts (plan summaries, lesson content)

**Streaming with timestamps:** `POST /v1/text-to-speech/{voice_id}/stream_with_timestamps`
- Returns: JSON stream with base64 audio + character timing
- Useful for karaoke-style highlighting (accessibility feature)

### 1.3 Python SDK

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="YOUR_API_KEY")

# Non-streaming
audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Hello world",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)

# Streaming
stream = client.text_to_speech.stream(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Long text...",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)
```

Package: `elevenlabs` (pip/uv installable)

### 1.4 Authentication

- Header: `xi-api-key: <API_KEY>`
- Env var (SDK): `ELEVEN_API_KEY`
- Our adapter already uses `xi-api-key` header correctly

### 1.5 Output Formats

| Format | Description | Tier Required |
|--------|-------------|---------------|
| `mp3_22050_32` | Low quality MP3 | Free |
| `mp3_44100_128` | High quality MP3 (default) | Free |
| `mp3_44100_192` | HQ MP3 | Creator+ |
| `pcm_16000` | PCM 16kHz | Free |
| `pcm_44100` | PCM 44.1kHz | Pro+ |
| `opus_48000_128` | Opus (web) | Free |

**Recommendation:** Use `mp3_44100_128` as default (our current adapter does this). Offer `opus_48000_128` as alternative for web playback (smaller files).

### 1.6 Subscription & Limits (from live API query)

- **Tier:** Creator ($22/mo)
- **Character limit:** 100,000/month
- **Characters used:** 6,010 (~6% used)
- **Voice slots:** 4/30 used
- **Reset period:** Monthly

### 1.7 Available Voices (from live API query)

| Voice ID | Name | Category |
|----------|------|----------|
| `bIHbv24MWmeRgasZH58o` | Will - Relaxed Optimist | premade |
| `GBv7mTt0atIp3Br8iCZE` | Thomas | premade |
| `pMsXgVXv3BLzUgSXRplE` | Serena | premade |
| `EXAVITQu4vr4xnSDxMaL` | Sarah - Mature, Reassuring | premade |
| `yoZ06aMxZJJ28mfd3POQ` | Sam | premade |
| `CwhRBWXzGAHq8TQ4Fs17` | Roger - Laid-Back, Casual | premade |
| `SAz9YHcvj6GT2YYXdXww` | River - Relaxed, Neutral | premade |
| `N2uMOnZaiuVAu6FhRqcd` | Rafael Bittencourt | cloned |
| `u8iOUYmHDmFe99GSmk6A` | Rafael (PodCast) | cloned |
| `21m00Tcm4TlvDq8ikWAM` | Rachel | premade |

**Recommendation for locale mapping:**
- EN: `EXAVITQu4vr4xnSDxMaL` (Sarah - professional, reassuring)
- PT-BR: `N2uMOnZaiuVAu6FhRqcd` (Rafael Bittencourt - cloned Brazilian voice) or `SAz9YHcvj6GT2YYXdXww` (River - neutral)
- ES: `pMsXgVXv3BLzUgSXRplE` (Serena) or use multilingual model with `language_code="es"`

### 1.8 Existing Code in AiLine

**Already implemented:**
- `runtime/ailine_runtime/domain/ports/media.py:16-21` — TTS Protocol: `synthesize(text, locale, speed) -> bytes`
- `runtime/ailine_runtime/adapters/media/elevenlabs_tts.py` — ElevenLabsTTS adapter (httpx-based, uses v1 REST API directly)
- `runtime/ailine_runtime/adapters/media/fake_tts.py` — FakeTTS for testing (returns silent WAV)
- Tests exist in `runtime/tests/test_elevenlabs_tts.py` and `runtime/tests/test_container_elevenlabs_sign.py`

**NOT implemented:**
- No API endpoint (POST /media/tts)
- No streaming support
- No 3-tier fallback (Chatterbox/Kokoro adapters missing)
- No frontend audio player component
- Model is hardcoded to `eleven_multilingual_v2` (should upgrade to `eleven_v3`)

### 1.9 Implementation Plan for F-165

1. Upgrade adapter: `eleven_multilingual_v2` -> `eleven_v3` (74 languages)
2. Add `language_code` parameter to API call (ISO 639-1)
3. Add streaming support: `stream_text_to_speech()` method
4. Create `POST /media/tts` endpoint: `{ text, locale, voice_preset?, format? }`
5. Add circuit breaker wrapper (existing pattern)
6. Build FallbackTTSAdapter chain (ElevenLabs -> stub for Chatterbox -> stub for Kokoro)
7. Frontend: audio player component with play/pause/speed controls
8. Frontend: "Read Aloud" button on plan results and tutor responses

---

## 2. BRF Braille Format

### 2.1 What is BRF?

BRF (Braille Ready Format) is a plain text file format for Braille documents. Each character in the file maps to a specific Braille cell using the North American Braille Computer Code (NABCC).

### 2.2 ASCII-Braille Character Mapping (NABCC)

The mapping uses ASCII characters 32-95 (space through underscore) to represent Braille cells:

| ASCII | Dots | Braille | Notes |
|-------|------|---------|-------|
| Space (32) | (none) | Empty cell | |
| A (65) | 1 | ⠁ | Also digit 1 with number sign |
| B (66) | 1,2 | ⠃ | Also digit 2 |
| C (67) | 1,4 | ⠉ | Also digit 3 |
| ... | ... | ... | Full alphabet follows standard Braille pattern |
| 1 (49) | 2 | ⠂ | Number indicator prefix required |
| , (44) | 2 | ⠂ | Context-dependent |
| . (46) | 2,5,6 | ⠲ | Period |

Key control characters:
- `#` (number indicator) precedes digits
- `,` (capital letter indicator) precedes uppercase
- `,,` (double capital) for all-caps words
- `;` (letter indicator) returns to letter mode after numbers

### 2.3 Grade 1 (Uncontracted) Braille

- One-to-one letter mapping: each print letter = one Braille cell
- Number sign before digits
- Capital indicator before uppercase letters
- Simplest to implement programmatically
- Used for: beginners, technical content, code, foreign languages

### 2.4 Grade 2 (Contracted) Braille

- Uses 189 contractions (abbreviations) to save space
- Single-cell contractions: `b` = "but", `c` = "can", `d` = "do", `e` = "every", etc.
- Multi-cell contractions: `ing`, `tion`, `ness`, etc.
- Context-dependent rules (beginning/middle/end of word)
- Significantly more complex to implement correctly
- Used for: most published Braille materials

### 2.5 Page Format

Standard BRF page format:
- **Width:** 40 cells per line (standard Braille display width)
- **Height:** 25 lines per page (standard embosser page)
- **Form feed:** ASCII 12 (FF) separates pages
- **Line ending:** CR+LF (Windows) or LF (Unix)
- **File extension:** `.brf`
- **Encoding:** ASCII (7-bit)

### 2.6 Multi-Language Support

| Language | Standard | Library Support |
|----------|----------|-----------------|
| English | UEB (Unified English Braille) | liblouis: `en-ueb-g1.ctb`, `en-ueb-g2.ctb` |
| Portuguese (BR) | BNCC Braille (pt-BR) | liblouis: `pt.ctb`, `pt-comp8.ctb` |
| Spanish | ONCE Spanish Braille | liblouis: `es-g1.ctb`, `es-g2.ctb` |

### 2.7 Implementation Approach

**Phase 1 (Sprint 25):** Grade 1 English only
- Direct ASCII-Braille mapping (simple character table)
- Number sign, capital indicator
- No external library needed for Grade 1
- BRF file generation with 40x25 page format

**Phase 2 (Sprint 26):** Grade 2 + i18n
- Use liblouis for Grade 2 contractions and Portuguese/Spanish tables
- liblouis handles the complex contraction rules

---

## 3. Python Braille Libraries

### 3.1 liblouis

- **Repository:** github.com/liblouis/liblouis
- **Python binding:** `python-louis` (pip: `louis`)
- **Description:** The most comprehensive open-source Braille translator
- **Features:**
  - Grade 1 and Grade 2 for 100+ languages
  - UEB (Unified English Braille)
  - Portuguese, Spanish, French, German tables
  - Forward and backward translation
  - Emphasis handling (bold, italic)
  - C library with Python bindings via ctypes
- **License:** LGPL-2.1+
- **Status:** Actively maintained (latest release 2025)
- **Installation:** `pip install louis` (requires liblouis C library installed)
- **Docker:** Available via `apt-get install liblouis-dev liblouis-bin`

**Usage:**
```python
import louis

# Grade 1 English
result = louis.translateString(["en-ueb-g1.ctb"], "Hello World")

# Grade 2 English
result = louis.translateString(["en-ueb-g2.ctb"], "Hello World")

# Portuguese
result = louis.translateString(["pt.ctb"], "Olá Mundo")
```

### 3.2 pybraille

- **Repository:** github.com/AnirudhG07/pybraille (or similar)
- **Description:** Pure Python Braille translator (no C dependencies)
- **Features:**
  - Grade 1 English only
  - Basic ASCII-Braille mapping
  - Simple API
- **Limitations:** No Grade 2, no i18n, less maintained
- **License:** MIT
- **Status:** Small project, limited maintenance

### 3.3 Recommendation

- **Sprint 25 (Grade 1 English):** Implement our own ASCII-Braille mapping (simple, no external deps, ~100 lines)
- **Sprint 26 (Grade 2 + i18n):** Integrate liblouis via `python-louis` package
  - Add `liblouis-dev` to Dockerfile: `RUN apt-get install -y liblouis-dev`
  - Add `louis` to pyproject.toml

---

## 4. Skills System Interfaces (DB-Backing Analysis)

### 4.1 Current Architecture (Filesystem-Based)

```
skills/                          # 17 SKILL.md files
  accessibility-adaptor/SKILL.md
  lesson-planner/SKILL.md
  ...
```

**Key Classes:**

1. **`SkillDefinition`** (`registry.py:10-16`)
   - Fields: `name: str`, `description: str`, `instructions: str`, `metadata: dict[str, str]`
   - Pure Pydantic model — maps directly to a DB table

2. **`SkillRegistry`** (`registry.py:19-86`)
   - In-memory dict: `_skills: dict[str, SkillDefinition]`
   - Methods: `scan(directory)`, `get_by_name(name)`, `list_names()`, `get_prompt_fragment(names)`
   - **DB replacement:** SkillRepository port with CRUD + vector similarity search

3. **`parse_skill_md()`** (`loader.py:15-72`)
   - Parses YAML frontmatter + markdown body from SKILL.md files
   - **DB replacement:** Still needed for initial seed migration (load filesystem skills -> DB)

4. **`validate_skill_spec()`** (`spec.py:86-196`)
   - Validates against agentskills.io spec
   - **DB replacement:** Validate on CREATE/UPDATE API calls (input validation layer)

5. **`SkillPromptComposer` / `compose_skills_fragment()`** (`composer.py:103-195`)
   - Takes `list[ActivatedSkill]`, applies token budget, returns prompt fragment
   - **DB replacement:** Input changes from `ActivatedSkill` (filesystem) to DB-fetched skills
   - The composer itself stays the same — it operates on ActivatedSkill objects regardless of source

6. **`AccessibilityPolicy`** (`accessibility_policy.py:122-265`)
   - Hardcoded mapping: 7 profiles -> 17 skill slugs
   - `resolve_accessibility_skills(needs, max_skills)` -> ordered list
   - **DB replacement:** Policy itself stays hardcoded (deterministic mapping table). But the `available_skills` filter should query the DB to check which skills exist.

### 4.2 DB Schema Proposal

```sql
-- Skill table (replaces filesystem SKILL.md)
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    slug VARCHAR(64) UNIQUE NOT NULL,          -- name from SKILL.md
    description TEXT NOT NULL,
    instructions_md TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',       -- dict[str, str]
    license VARCHAR(255),
    compatibility VARCHAR(500),
    allowed_tools TEXT,                          -- space-delimited
    embedding VECTOR(1536),                     -- pgvector for similarity search
    teacher_id UUID REFERENCES users(id),       -- NULL = system skill
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_skills_teacher ON skills(teacher_id);
CREATE INDEX idx_skills_embedding ON skills USING hnsw (embedding vector_cosine_ops);

-- Skill version history
CREATE TABLE skill_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    instructions_md TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(skill_id, version)
);

-- Teacher skill sets (presets)
CREATE TABLE teacher_skill_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    teacher_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    skill_slugs TEXT[] NOT NULL,                 -- array of skill slugs
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(teacher_id, name)
);
```

### 4.3 SkillRepository Port

```python
class SkillRepository(Protocol):
    """Port for skill persistence."""

    async def get_by_slug(self, slug: str) -> SkillDefinition | None: ...
    async def list_all(self, *, active_only: bool = True) -> list[SkillDefinition]: ...
    async def search(self, query: str, *, limit: int = 10) -> list[SkillDefinition]: ...
    async def search_similar(self, embedding: list[float], *, limit: int = 5) -> list[SkillDefinition]: ...
    async def create(self, skill: SkillDefinition, *, teacher_id: str | None = None) -> str: ...
    async def update(self, slug: str, skill: SkillDefinition) -> None: ...
    async def delete(self, slug: str) -> None: ...
    async def list_by_teacher(self, teacher_id: str) -> list[SkillDefinition]: ...
```

### 4.4 Migration Strategy

1. Create migration 0004 with skills/skill_versions/teacher_skill_sets tables
2. Seed migration: scan filesystem skills/ directory, parse each SKILL.md, insert into skills table
3. Generate embeddings via gemini-embedding-001 for each skill's description+instructions
4. Update SkillRegistry to optionally use DB (adapter pattern)
5. Keep filesystem scan as fallback for development without DB

---

## 5. Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| TTS model | `eleven_v3` | 74 languages, newest, best quality |
| TTS fallback | Flash v2.5 | Low latency, 32 languages |
| TTS output format | `mp3_44100_128` | Good quality, widely supported |
| Braille Grade 1 impl | Custom (no deps) | Simple mapping, ~100 LOC |
| Braille Grade 2 impl | liblouis (Sprint 26) | Industry standard, 100+ languages |
| BRF page format | 40x25 | Standard Braille display/embosser |
| Skills DB PK | UUID v7 | Consistent with existing tables |
| Skills embedding | VECTOR(1536) | Match existing gemini-embedding-001 dimension |
| Skills HNSW index | vector_cosine_ops | Standard for semantic similarity |
