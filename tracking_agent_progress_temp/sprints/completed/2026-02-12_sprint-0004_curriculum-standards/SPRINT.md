# Sprint 0004 — Curriculum Standards

**Status:** planned | **Date:** 2026-02-12
**Goal:** Real BNCC (Brazil) + CCSS/NGSS (US) curriculum data with unified search.
Enable the `curriculum_lookup` tool to return real standards instead of stubs.

---

## Scope & Acceptance Criteria

Import Brazilian BNCC and US CCSS/NGSS curriculum standards as structured JSON
data files. Build a grade equivalency mapping between Brazilian and US systems
(including subject equivalency). Implement `CurriculumProvider` adapters (BNCC,
US, Unified) that satisfy the existing `CurriculumProvider` protocol in
`domain/ports/curriculum.py`. Replace the stub `curriculum_lookup_handler` in
`tools/registry.py` with a real implementation backed by these adapters. After
this sprint, any LangGraph agent node that calls the `curriculum_lookup` tool
receives real curriculum objectives.

---

## Research Findings (Confirmed Sources)

### BNCC API Source (confirmed)
- **Base URL:** `https://cientificar1992.pythonanywhere.com/api/v1/`
- **Endpoints:**
  - `GET /componentes` -- list all curriculum components
  - `GET /habilidades?componente=<X>&ano=<Y>` -- objectives by component and year
- **Ensino Fundamental II components (6o-9o):** Matematica, Lingua Portuguesa,
  Ciencias, Historia, Geografia, Arte, Educacao Fisica, Ingles
- **Ensino Medio (1a-3a serie):** Must also be scraped from the same API.
  EM components vary (Linguagens, Matematica, Ciencias da Natureza, Ciencias
  Humanas); enumerate via `/componentes` with EM year parameters.

### US Standards Source (confirmed)
- **Primary:** StandardX dataset (`galacticpolymath/standardX` on GitHub)
  - CCSS Math: code format `CCSS.MATH.CONTENT.6.NS.A.1`
  - CCSS ELA: code format `CCSS.ELA-LITERACY.RL.6.1`
  - NGSS Middle School: code format `MS-PS1-2`
  - NGSS High School: code format `HS-LS1-1`
- **Fallback:** Common Core State Standards Initiative website (corestandards.org)
- Import script attempts StandardX first, falls back to web scraping, and
  documents which source was used in output JSON metadata.

### Grade Equivalency (confirmed)
- Brazil 6o ano = US Grade 6
- Brazil 7o ano = US Grade 7
- Brazil 8o ano = US Grade 8
- Brazil 9o ano = US Grade 9
- Brazil 1a serie EM = US Grade 10
- Brazil 2a serie EM = US Grade 11
- Brazil 3a serie EM = US Grade 12

### Subject Equivalency (confirmed)
- Matematica <-> Math
- Lingua Portuguesa <-> ELA (English Language Arts)
- Ciencias <-> Science (NGSS alignment)

### Unified Schema (canonical)
All curriculum entries across BNCC/CCSS/NGSS conform to the `CurriculumObjective`
Pydantic entity and are stored as JSON with this shape:
```json
{
  "code": "EF06MA01",
  "system": "bncc",
  "subject": "math",
  "grade": "6",
  "domain": "Numeros",
  "description": "Comparar, ordenar...",
  "keywords": ["fracoes", "numeros"]
}
```
The `system` field discriminates origin (`bncc`, `ccss`, `ngss`). The `grade`
field uses a normalized short form (e.g., `"6"` for 6o ano / Grade 6) to enable
cross-system queries. Each provider maps its raw grade labels to this normalized
form on import; the grade_mapping.json provides the lookup tables.

---

## Stories

### S4-001: Scrape/Import BNCC Standards to JSON [ ]

**Description:** Extract BNCC (Base Nacional Comum Curricular) objectives for
grades 6-12 (Ensino Fundamental II + Ensino Medio) from the confirmed API
source. The BNCC is Brazil's national curriculum framework organized by year,
subject area (componente), and individual learning objectives identified by
alphanumeric codes (e.g., EF06MA01 = Ensino Fundamental, 6o ano, Matematica,
objective 01; EM13MAT101 = Ensino Medio, competencia area, Matematica).

Store as structured JSON with codes, descriptions, grades, subjects, keywords,
and knowledge area. Content must remain in Portuguese (the original BNCC
language) to preserve pedagogical precision.

**Files:**
- `runtime/ailine_runtime/data/curriculum/bncc.json` -- structured data file
- `runtime/scripts/import_bncc.py` -- reproducible import/processing script

**Data schema (each entry, aligned with CurriculumObjective entity):**
```json
{
  "code": "EF06MA01",
  "system": "bncc",
  "subject": "Matematica",
  "grade": "6",
  "domain": "Numeros",
  "description": "Comparar, ordenar, ler e escrever numeros naturais...",
  "keywords": ["numeros naturais", "comparacao", "ordenacao"]
}
```
Note: `grade` uses normalized short form (`"6"`, `"7"`, ..., `"10"`, `"11"`,
`"12"`) to enable cross-system queries. The import script maps raw API labels
(e.g., "6o ano", "1a serie EM") to these normalized values.

**Acceptance Criteria:**
- [ ] JSON file with approximately 1500 BNCC objectives
- [ ] Covers Ensino Fundamental II subjects (all 8): Matematica, Lingua
      Portuguesa, Ciencias, Historia, Geografia, Arte, Educacao Fisica, Ingles
- [ ] Covers Ensino Medio (1a-3a serie): all available components from the API
      (Linguagens, Matematica, Ciencias da Natureza, Ciencias Humanas, etc.)
- [ ] Grades: 6o ao 9o Fundamental II (EF) + 1a ao 3a serie Ensino Medio (EM)
- [ ] Each entry has all CurriculumObjective fields: code, system, subject,
      grade, domain, description, keywords (list)
- [ ] `system` field is always `"bncc"` for all entries
- [ ] All content in Portuguese (original BNCC language)
- [ ] Import script is reproducible: `uv run python runtime/scripts/import_bncc.py`
      regenerates the JSON from the API source
- [ ] Validates against `CurriculumObjective` Pydantic model on load
- [ ] File is valid JSON, UTF-8 encoded, sorted by code

**Technical notes:**
- BNCC code structure: `EF` (Ensino Fundamental) or `EM` (Ensino Medio) +
  `06` (year) + `MA` (subject abbreviation) + `01` (sequence number)
- EM codes may follow a different pattern (e.g., `EM13MAT101` for competencia-
  based structure); the import script must handle both EF and EM code formats.
- Source: MEC official BNCC documents (basenacionalcomum.mec.gov.br)
- If the API or MEC website structure has changed, fall back to curated open
  datasets or manual extraction from the official PDF

**Confirmed source API:** `https://cientificar1992.pythonanywhere.com/api/v1/`
- Endpoints: `/componentes` (list all curriculum components),
  `/habilidades?componente=<X>&ano=<Y>` (objectives filtered by component and year)
- **Ensino Fundamental II (6o-9o):** Scrape all 8 components: Matematica, Lingua
  Portuguesa, Ciencias, Historia, Geografia, Arte, Educacao Fisica, Ingles
- **Ensino Medio (1a-3a serie):** Also scrape all available EM components.
  Enumerate EM components via `/componentes` with EM year parameters. EM may
  use area-based organization (Linguagens, Matematica, Ciencias da Natureza,
  Ciencias Humanas) rather than individual subjects.
- Import script algorithm:
  1. `GET /componentes` to discover all available components
  2. For each component, iterate years 6-9 (EF) and 1-3 (EM)
  3. `GET /habilidades?componente=<X>&ano=<Y>` for each combination
  4. Map API response fields to CurriculumObjective schema
  5. Normalize grade labels to short form
  6. Write sorted, deduplicated JSON output
- Static JSON output only -- no runtime API dependency (ADR-005). The import
  script fetches from the API at build/dev time and produces the static JSON.

---

### S4-002: Process US Standards to JSON [ ]

**Description:** Import Common Core State Standards (CCSS) for Mathematics and
English Language Arts, plus Next Generation Science Standards (NGSS) into
structured JSON. CCSS is the dominant US curriculum framework for Math/ELA
grades K-12. NGSS covers science across grade bands (K-2, 3-5, 6-8, 9-12).

**Files:**
- `runtime/ailine_runtime/data/curriculum/ccss.json` -- CCSS Math + ELA
- `runtime/ailine_runtime/data/curriculum/ngss.json` -- NGSS Science
- `runtime/scripts/import_us_standards.py` -- reproducible import script

**CCSS data schema (each entry, aligned with CurriculumObjective entity):**
```json
{
  "code": "CCSS.MATH.CONTENT.6.RP.A.1",
  "system": "ccss",
  "subject": "Math",
  "grade": "6",
  "domain": "Ratios and Proportional Relationships",
  "description": "Understand the concept of a ratio...",
  "keywords": ["ratio", "quantities", "relationship"]
}
```

**NGSS data schema (each entry, aligned with CurriculumObjective entity):**
```json
{
  "code": "MS-PS1-1",
  "system": "ngss",
  "subject": "Science",
  "grade": "6-8",
  "domain": "Matter and its Interactions",
  "description": "Develop models to describe the atomic composition...",
  "keywords": ["atoms", "molecules", "models"]
}
```
Note: NGSS `grade` uses band notation (`"6-8"`, `"9-12"`) since NGSS standards
span grade bands. The provider normalizes searches so a query for grade `"7"`
matches the `"6-8"` band.

**Acceptance Criteria:**
- [ ] CCSS file with approximately 700 standards
  - Math: K-8 grade-specific + high school conceptual categories
  - ELA: K-5 grade-specific + 6-12 grade band standards
  - Each entry: code (dot notation), description, grade, subject, domain
- [ ] NGSS file with approximately 300 standards
  - Grade bands: K-2, 3-5, 6-8, 9-12
  - Each entry: code, description, grade band, disciplinary core idea, domain
- [ ] All content in English
- [ ] Import script reproducible: `uv run python runtime/scripts/import_us_standards.py`
- [ ] Validates against `CurriculumObjective` Pydantic model on load
- [ ] Files are valid JSON, UTF-8 encoded, sorted by code

**Technical notes:**
- CCSS code structure: `CCSS.MATH.CONTENT.6.RP.A.1` (standard.domain.grade.cluster.standard)
- NGSS code structure: `MS-PS1-1` (grade-band + disciplinary-core-idea + number)
- Sources: corestandards.org (CCSS), nextgenscience.org (NGSS)

**Confirmed primary source:** StandardX dataset (`galacticpolymath/standardX` on GitHub)
- CCSS Math grades 6-12: code format `CCSS.MATH.CONTENT.6.NS.A.1`
- CCSS ELA grades 6-12: code format `CCSS.ELA-LITERACY.RL.6.1`
- NGSS Middle School + High School: code format `MS-PS1-2`, `HS-LS1-1`
- **Fallback:** If StandardX is unavailable or incomplete, scrape directly from
  the Common Core State Standards Initiative website (corestandards.org) using
  the import script.
- The import script should attempt StandardX first, then fall back to web
  scraping, and document which source was used in the output JSON metadata.

---

### S4-003: Grade Equivalency Mapping [ ]

**Description:** Create a bidirectional grade mapping between Brazilian
educational grades (1o-9o Fundamental + 1o-3o Medio) and US grades (K-12).
This enables cross-system curriculum alignment: when a teacher specifies
"6o Fundamental II" we can look up equivalent US Grade 6 standards, and
vice versa. Includes age ranges to support fuzzy matching.

**Files:**
- `runtime/ailine_runtime/data/curriculum/grade_mapping.json`

**Data schema:**
```json
{
  "grade_mappings": [
    {
      "normalized_grade": "6",
      "br_grade": "6o Fundamental II",
      "br_grade_aliases": ["6o ano", "6 ano", "sexto ano"],
      "us_grade": "Grade 6",
      "us_grade_aliases": ["6th grade", "sixth grade", "grade 6"],
      "age_range": "11-12",
      "br_level": "Fundamental II",
      "us_level": "Middle School"
    }
  ],
  "subject_mappings": [
    {
      "normalized": "math",
      "br": "Matematica",
      "br_aliases": ["Matematica e suas Tecnologias"],
      "us": "Math",
      "us_aliases": ["Mathematics"]
    },
    {
      "normalized": "ela",
      "br": "Lingua Portuguesa",
      "br_aliases": ["Linguagens e suas Tecnologias", "Portugues"],
      "us": "ELA",
      "us_aliases": ["English Language Arts", "Reading", "Writing"]
    },
    {
      "normalized": "science",
      "br": "Ciencias",
      "br_aliases": ["Ciencias da Natureza e suas Tecnologias"],
      "us": "Science",
      "us_aliases": ["NGSS"]
    },
    {
      "normalized": "history",
      "br": "Historia",
      "br_aliases": ["Ciencias Humanas e Sociais Aplicadas"],
      "us": "Social Studies",
      "us_aliases": ["History"]
    },
    {
      "normalized": "geography",
      "br": "Geografia",
      "br_aliases": [],
      "us": "Geography",
      "us_aliases": []
    }
  ],
  "br_to_us": {
    "6": "6", "7": "7", "8": "8", "9": "9",
    "10": "10", "11": "11", "12": "12"
  },
  "us_to_br": {
    "6": "6", "7": "7", "8": "8", "9": "9",
    "10": "10", "11": "11", "12": "12"
  }
}
```
Note: The `normalized_grade` field in `grade_mappings` is the canonical short
form used in all JSON data files. The `br_to_us` and `us_to_br` dictionaries
use normalized grades as keys for O(1) lookup. Subject mappings use a
`normalized` key that matches the value stored in curriculum JSON entries.

**Acceptance Criteria:**
- [ ] Bidirectional grade mapping: BR grade to US grade and vice versa
- [ ] Bidirectional subject mapping: BR subject to US subject and vice versa
- [ ] Covers full range: Pre-escola/Kindergarten through 3o Medio/Grade 12
- [ ] Age ranges included for each grade level
- [ ] Aliases for fuzzy matching (e.g., "6th grade", "sexto ano", "6o ano")
- [ ] Brazilian levels: Educacao Infantil, Fundamental I (1o-5o),
      Fundamental II (6o-9o), Ensino Medio (1o-3o)
- [ ] US levels: Elementary (K-5), Middle School (6-8), High School (9-12)
- [ ] Subject mappings include normalized keys + aliases for both systems
- [ ] Valid JSON, UTF-8 encoded

**Technical notes:**
- Brazilian and US systems are not 1:1 for all grades. Pre-escola maps
  approximately to Pre-K/Kindergarten. Ensino Medio 1o-3o maps to Grades 10-12.
- Aliases support the `UnifiedProvider.search()` fuzzy grade resolution.
- Subject aliases handle EM area-based naming (e.g., "Matematica e suas
  Tecnologias" -> normalized "math").

**Confirmed grade mapping (core range for this sprint):**
- 6o ano = Grade 6, 7o ano = Grade 7, 8o ano = Grade 8, 9o ano = Grade 9
- 1a serie EM = Grade 10, 2a serie EM = Grade 11, 3a serie EM = Grade 12

**Confirmed subject equivalency mapping:**
- Matematica <-> Math (normalized: `"math"`)
- Lingua Portuguesa <-> ELA (normalized: `"ela"`)
- Ciencias <-> Science / NGSS alignment (normalized: `"science"`)
- Historia <-> Social Studies (normalized: `"history"`)
- Geografia <-> Geography (normalized: `"geography"`)

**Extensibility:** The mapping format must support future country additions
(e.g., UK Key Stages, IB curriculum) without schema changes. Use a
country-keyed structure or a flat list with `country` field so new systems
can be appended without restructuring existing data.

---

### S4-004: CurriculumProvider Adapters [ ]

**Description:** Implement three concrete adapters that satisfy the
`CurriculumProvider` protocol defined in `domain/ports/curriculum.py`:

1. **BNCCProvider** -- searches BNCC JSON data
2. **USStandardsProvider** -- searches CCSS + NGSS JSON data
3. **UnifiedCurriculumProvider** -- searches across all systems with automatic
   grade equivalency resolution

Each adapter loads its JSON data file(s) into memory on initialization and
provides search, lookup-by-code, and list capabilities.

**Existing protocol (from `domain/ports/curriculum.py`):**
```python
class CurriculumProvider(Protocol):
    async def search(
        self, query: str, *, grade: str | None = None,
        subject: str | None = None, system: str | None = None,
    ) -> list[CurriculumObjective]: ...

    async def get_by_code(self, code: str) -> CurriculumObjective | None: ...

    async def list_standards(self, *, system: str | None = None) -> list[str]: ...
```

**Files:**
- `runtime/ailine_runtime/adapters/curriculum/bncc_provider.py`
- `runtime/ailine_runtime/adapters/curriculum/us_provider.py`
- `runtime/ailine_runtime/adapters/curriculum/unified_provider.py`
- `runtime/ailine_runtime/adapters/curriculum/__init__.py` (update exports)

**BNCCProvider design:**
- Loads `data/curriculum/bncc.json` as `list[CurriculumObjective]` at startup
- Builds a `dict[str, CurriculumObjective]` index keyed by `code` for O(1) lookup
- `search()`: keyword match on description + keywords fields, filtered by
  grade/subject. Returns top-N matches ranked by relevance (keyword hit count).
  Keywords are tokenized and matched case-insensitively against the objective's
  `description` and `keywords` list.
- `get_by_code()`: exact code lookup via dict index
- `list_standards()`: returns all unique BNCC codes

**USStandardsProvider design:**
- Loads both `data/curriculum/ccss.json` and `data/curriculum/ngss.json`
  as `list[CurriculumObjective]` at startup
- Builds a combined code index across both datasets
- `search()`: keyword match with optional system filter ("ccss" or "ngss")
- `get_by_code()`: exact lookup across both datasets
- `list_standards(system="ccss")`: filter by CCSS or NGSS

**UnifiedCurriculumProvider design:**
- Wraps BNCCProvider + USStandardsProvider
- Loads `data/curriculum/grade_mapping.json` for cross-system grade and subject
  resolution
- `search(query, grade="6")`: delegates to all child providers with the
  normalized grade. If grade is provided as an alias (e.g., "6th grade",
  "6o ano"), resolves it to normalized form first.
- `search(query, subject="Matematica")`: resolves subject alias to normalized
  form ("math") and filters across all providers.
- Results tagged with source system for caller disambiguation
- Grade alias resolution: "6th grade" -> normalized "6" -> searches both
  BNCC (6o Fundamental II) and CCSS/NGSS (Grade 6)
- Subject alias resolution: "Matematica" -> normalized "math" -> searches
  both BNCC and CCSS Math standards
- `get_by_code("EF06MA01")`: dispatches to correct provider based on code
  prefix pattern (EF/EM -> BNCC, CCSS -> US CCSS, MS/HS -> US NGSS)

**Acceptance Criteria:**
- [ ] `BNCCProvider` satisfies `CurriculumProvider` protocol
  - `search("numeros naturais", grade="6o Fundamental II")` returns matching BNCC objectives
  - `get_by_code("EF06MA01")` returns exact CurriculumObjective
  - `list_standards()` returns all BNCC codes
- [ ] `USStandardsProvider` satisfies `CurriculumProvider` protocol
  - `search("ratio", grade="Grade 6", system="ccss")` returns CCSS matches
  - `get_by_code("MS-PS1-1")` returns NGSS objective
  - `list_standards(system="ngss")` returns only NGSS codes
- [ ] `UnifiedCurriculumProvider` satisfies `CurriculumProvider` protocol
  - `search("fractions", grade="5o Fundamental I")` returns BNCC + CCSS Grade 5 results
  - Grade alias resolution works ("5th grade" finds both systems)
  - Results include `system` field indicating BNCC vs CCSS vs NGSS origin
- [ ] All adapters pass `isinstance(adapter, CurriculumProvider)` check
- [ ] Unit tests for each adapter with representative data

**Technical notes:**
- Search is in-memory (no external search engine for MVP). JSON files are small
  enough (~2500 objectives total) to load entirely.
- Keyword matching: simple case-insensitive substring/token overlap. More
  sophisticated search (TF-IDF, embeddings) is a post-MVP enhancement.
- Thread safety: data is read-only after init; no locking needed.

**UnifiedProvider aggregation pattern:**
- `UnifiedCurriculumProvider` wraps all individual providers and delegates
  searches across all registered systems.
- Each provider loads from static JSON at startup. No lazy loading, no
  runtime API calls. Data is read-only after init.
- `search()`: keyword match + grade filter + subject filter, aggregated from
  all child providers. Results are merged and ranked by relevance score.
  Grade and subject aliases are resolved to normalized forms before dispatch.
- `get_by_code("EF06MA01")`: exact match dispatched to the correct provider
  based on code prefix pattern (EF/EM -> BNCC, CCSS -> US CCSS, MS/HS -> NGSS).
- `search()` fuzzy keyword matching: case-insensitive token overlap between
  query terms and each objective's `description` + `keywords` fields. Score =
  number of matching tokens. Results sorted by descending score.
- **Input:** topic (str), grade_level (str|None), subject (str|None),
  curriculum_system (str|None, e.g., "bncc", "ccss", "ngss")
- **Output:** list of matching CurriculumObjective with codes and descriptions
- **Primary consumers:** `curriculum_lookup` tool in the executor agent +
  tutor RAG enrichment pipeline (when the tutor needs curriculum context to
  ground its responses).

---

### S4-005: Update curriculum_lookup Tool [ ]

**Description:** Replace the stub `curriculum_lookup_handler` in
`tools/registry.py` with a real implementation backed by the
`UnifiedCurriculumProvider`. Update the `CurriculumLookupArgs` schema to support
the full parameter set (query, grade, standard_system, subject).

The current stub returns `{"objectives": [], "note": "stub_curriculum_lookup"}`.
After this story, it returns real curriculum objectives from BNCC/CCSS/NGSS data.

**Files:**
- `runtime/ailine_runtime/tools/registry.py` (update args model + handler)
- `runtime/ailine_runtime/shared/container.py` (register UnifiedCurriculumProvider)

**Current stub (to be replaced):**
```python
# In runtime/ailine_runtime/tools/registry.py
class CurriculumLookupArgs(BaseModel):
    standard: str = Field(..., description="BNCC|US")
    grade: str = Field(..., description="Serie/ano")
    topic: str = Field(..., description="Tema/topico")

async def curriculum_lookup_handler(args: CurriculumLookupArgs) -> dict:
    return {"objectives": [], "note": "stub_curriculum_lookup"}
```

**New implementation:**
```python
# In runtime/ailine_runtime/tools/registry.py
class CurriculumLookupArgs(BaseModel):
    query: str = Field(
        ...,
        description="Search query: topic, keyword, or objective description "
                    "(e.g., 'fracoes', 'ratios', 'numeros naturais')",
    )
    grade_level: str | None = Field(
        None,
        description="Grade level, normalized or alias "
                    "(e.g., '6', '6o ano', '6th grade', 'Grade 6')",
    )
    subject: str | None = Field(
        None,
        description="Subject filter, normalized or alias "
                    "(e.g., 'math', 'Matematica', 'ELA', 'Science')",
    )
    curriculum_system: str | None = Field(
        None,
        description="Filter by system: 'bncc', 'ccss', 'ngss', or None for all",
    )
    max_results: int = Field(10, ge=1, le=50, description="Maximum results to return")

async def curriculum_lookup_handler(args: CurriculumLookupArgs) -> dict:
    provider = get_curriculum_provider()  # UnifiedCurriculumProvider from DI container
    objectives = await provider.search(
        args.query,
        grade=args.grade_level,
        subject=args.subject,
        system=args.curriculum_system,
    )
    return {
        "objectives": [obj.model_dump() for obj in objectives[:args.max_results]],
        "total_matches": len(objectives),
        "returned": min(len(objectives), args.max_results),
        "filters_applied": {
            "grade_level": args.grade_level,
            "curriculum_system": args.curriculum_system,
            "subject": args.subject,
        },
    }
```

**DI container registration (in `shared/container.py`):**
```python
# Register UnifiedCurriculumProvider as the CurriculumProvider singleton
from ..adapters.curriculum import (
    BNCCProvider, USStandardsProvider, UnifiedCurriculumProvider,
)

bncc = BNCCProvider()          # loads bncc.json at startup
us = USStandardsProvider()     # loads ccss.json + ngss.json at startup
unified = UnifiedCurriculumProvider(providers=[bncc, us])

container.register(CurriculumProvider, unified)
```

The `curriculum_lookup_handler` retrieves the `UnifiedCurriculumProvider`
from the container via `get_curriculum_provider()` helper (no global state;
dependency is injected at container build time).

**Acceptance Criteria:**
- [ ] `CurriculumLookupArgs` updated with: `query`, `grade_level`, `subject`,
      `curriculum_system` (optional), `max_results`
- [ ] Handler delegates to `UnifiedCurriculumProvider.search()` via DI container
- [ ] Returns structured JSON: `objectives` (list of CurriculumObjective dicts),
      `total_matches`, `returned`, `filters_applied`
- [ ] `UnifiedCurriculumProvider` registered as singleton in DI container
- [ ] Each provider loads its static JSON at startup (no lazy loading)
- [ ] Backward-compatible: Planner/Executor tool calls still work (old calls
      with `standard`/`topic` can be migrated via aliased field names or
      documented migration in the tool description)
- [ ] Tool description updated in `build_tool_registry()` to reflect new
      capabilities (bilingual, multi-system, grade/subject filtering)
- [ ] Integration test: call `curriculum_lookup` tool with representative
      queries and verify real BNCC + CCSS + NGSS objectives returned
- [ ] Error handling: invalid system name returns empty list with descriptive
      message, not an exception

---

## Dependencies

- **Sprint 1 (Clean Architecture):** Domain entities (`CurriculumObjective`,
  `CurriculumSystem`), port protocol (`CurriculumProvider`), DI container,
  tools registry. All must be in place.
- **Sprint 0 (Foundation):** API endpoints must be functional for end-to-end
  tool invocation via the LangGraph workflow.

---

## Decisions

- **ADR-005 (confirmed):** Static JSON for curriculum data. For hackathon scope,
  pre-processed JSON files loaded into memory are sufficient. No external
  database or search engine needed for approximately 2500 objectives. A
  post-MVP upgrade path is to embed objectives into pgvector for semantic
  search.
- **Search algorithm:** Simple keyword token matching for MVP. TF-IDF or
  embedding-based search is logged as a post-MVP enhancement in TODO.md.
- **Language preservation:** BNCC data stays in Portuguese; CCSS/NGSS in English.
  Cross-language search is not in scope (users query in the language of the
  standard system they target).

---

## Architecture Impact

```
runtime/ailine_runtime/
├── data/curriculum/
│   ├── bncc.json              # ~1500 objectives (Portuguese)
│   ├── ccss.json              # ~700 objectives (English)
│   ├── ngss.json              # ~300 objectives (English)
│   └── grade_mapping.json     # BR <-> US grade equivalency
├── adapters/curriculum/
│   ├── __init__.py            # Updated exports
│   ├── bncc_provider.py       # BNCCProvider (CurriculumProvider)
│   ├── us_provider.py         # USStandardsProvider (CurriculumProvider)
│   └── unified_provider.py    # UnifiedCurriculumProvider (CurriculumProvider)
├── scripts/
│   ├── import_bncc.py         # BNCC data extraction script
│   └── import_us_standards.py # CCSS/NGSS data extraction script
├── tools/
│   └── registry.py            # Updated curriculum_lookup handler
└── shared/
    └── container.py           # Register UnifiedCurriculumProvider
```

---

## Performance Characteristics

All curriculum data is loaded into memory at application startup. The total
dataset is small (~50-200 objectives per JSON file, ~2500 objectives total,
~1.25 MB combined). This design means:

- **Startup cost:** Negligible. Loading and indexing all JSON files takes <100ms.
- **Search latency:** In-memory keyword matching against the full dataset is
  sub-millisecond for typical queries. No network calls, no database round-trips.
- **No vector search needed:** For structured curriculum data with well-defined
  codes, grades, and subjects, keyword matching with field-level filtering is
  sufficient. Vector/semantic search adds complexity without meaningful benefit
  at this data scale and query pattern.
- **Hackathon/demo scope validated:** This approach is deliberately optimized for
  fast iteration and demo readiness. The post-MVP upgrade path (pgvector
  embeddings, see ADR-005) is documented but not needed until the objective
  count grows by 10x+ or cross-language semantic search becomes a requirement.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| BNCC data availability (MEC website structure may change) | Cannot import fresh data | Fall back to curated open datasets or manual extraction from official PDF; import script documents source |
| CCSS/NGSS source format changes | Cannot import US standards | Same fallback approach; pin a known-good data snapshot |
| Keyword search quality too low | Irrelevant results returned to agents | Add keyword weighting, test with representative queries, log search quality for post-MVP improvement |
| JSON data too large for memory | Slow startup | ~2500 entries at ~500 bytes each = ~1.25 MB; negligible for in-memory loading |
| Grade mapping edge cases (Pre-K, adult ed) | Unmapped grades return no cross-system results | Document known gaps; UnifiedProvider falls back to single-system search |

---

## Test Plan

- **Unit tests:** Each provider adapter tested with a small fixture dataset
  (5-10 objectives) verifying search, get_by_code, list_standards
- **Integration test:** Load full JSON files, run representative queries, assert
  non-empty results with correct schema
- **Tool test:** Invoke `curriculum_lookup` through the tool registry, verify
  real objectives returned (not stub)
- **Data validation test:** Load each JSON file, parse every entry as
  `CurriculumObjective`, assert zero validation errors
