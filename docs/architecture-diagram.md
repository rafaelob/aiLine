# AiLine Architecture Diagram

## 1. Hexagonal Architecture (Ports-and-Adapters)

```mermaid
graph TB
    subgraph External["External Clients"]
        Browser["Browser<br/>(Next.js 16 + React 19)"]
        Mobile["Mobile / PWA"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        direction TB
        FastAPI["FastAPI 0.129<br/>8 Routers + Middleware"]
        SSE["SSE Endpoints<br/>14 Event Types"]
        WS["WebSocket<br/>(Tutor + Libras)"]
        SQLAlchemy["SQLAlchemy 2.x Async<br/>11 Tables, UUID v7"]
        Alembic["Alembic Migrations"]
    end

    subgraph Application["Application Layer (Use Cases)"]
        PlanGen["Plan Generation"]
        TutorChat["Tutor Chat"]
        MatIngest["Material Ingestion"]
        RAGQuery["RAG Query"]
        SkillReg["Skill Registry<br/>11 Skills"]
    end

    subgraph Ports["Port Interfaces (Protocols)"]
        ChatLLM["ChatLLM"]
        Embeddings["Embeddings"]
        VectorStore["VectorStore"]
        UoW["UnitOfWork"]
        Curriculum["CurriculumProvider"]
        EventBus["EventBus"]
        STT["STT"]
        TTS["TTS"]
        SignRecog["SignRecognition"]
        ObjStore["ObjectStorage"]
    end

    subgraph Domain["Domain Core (Zero Framework Imports)"]
        Entities["Entities<br/>StudyPlan, Material,<br/>Tutor, Curriculum,<br/>Accessibility, Run"]
        ValueObj["Value Objects<br/>TeacherId, RunId,<br/>AccessibilityProfile"]
        DomainSvc["Domain Services<br/>Validators, Formatters"]
    end

    subgraph Adapters["Adapter Implementations"]
        Anthropic["Anthropic<br/>Claude Opus/Sonnet/Haiku"]
        OpenAI["OpenAI<br/>GPT-4o / GPT-4o-mini"]
        GeminiLLM["Gemini<br/>2.5 Flash / Pro"]
        GeminiEmbed["Gemini Embedding<br/>gemini-embedding-001<br/>1536d MRL"]
        PGVector["pgvector HNSW"]
        ChromaDB["ChromaDB"]
        FakeLLM["FakeLLM / FakeSTT<br/>FakeTTS (CI)"]
        WhisperSTT["Whisper V3 Turbo"]
        ElevenTTS["ElevenLabs TTS"]
        MediaPipe["MediaPipe + TF.js"]
    end

    subgraph Data["Data Stores"]
        Postgres["PostgreSQL 16<br/>+ pgvector 0.8"]
        Redis["Redis 7.x<br/>SSE Replay + Cache"]
    end

    Browser --> FastAPI
    Browser --> SSE
    Browser --> WS
    FastAPI --> Application
    SSE --> Application
    WS --> Application
    Application --> Ports
    Ports --> Domain
    Ports -.-> Adapters
    Adapters --> Data
    SQLAlchemy --> Postgres
    Alembic --> Postgres
```

## 2. Agent Pipeline (LangGraph + Pydantic AI)

```mermaid
graph LR
    subgraph Input
        Request["Teacher Request<br/>+ Accessibility Profile"]
    end

    subgraph FanOut["Parallel Fan-Out"]
        RAG["RAG Search<br/>(pgvector)"]
        Profile["Profile Analyzer<br/>(Accessibility needs)"]
    end

    subgraph Pipeline["Agent Pipeline (ailine_agents)"]
        Planner["PlannerAgent<br/>(Pydantic AI 1.58)<br/>StudyPlanDraft output"]
        QG["QualityGateAgent<br/>Score 0-100<br/>Structural checks"]
        Decision{{"Score >= 80?"}}
        Refine["Refine Loop<br/>(max 2 iterations)"]
        Executor["ExecutorAgent<br/>(Pydantic AI +<br/>LangGraph ToolNode)"]
        Export["Export Formatter<br/>(10 variants)"]
    end

    subgraph Output
        SSEStream["SSE Stream<br/>14 event types"]
    end

    Request --> RAG
    Request --> Profile
    RAG --> Planner
    Profile --> Planner
    Planner --> QG
    QG --> Decision
    Decision -- "No (< 80)" --> Refine
    Refine --> Planner
    Decision -- "Yes (>= 80)" --> Executor
    Executor --> Export
    Export --> SSEStream
```

## 3. RAG Pipeline

```mermaid
graph LR
    subgraph Ingest["Material Ingestion"]
        Upload["Upload<br/>(PDF/DOCX/TXT)"]
        Parse["Parse Document"]
        Chunk["Chunk<br/>512 tokens<br/>64 overlap"]
        Embed["Embed<br/>gemini-embedding-001<br/>1536d (MRL truncated)"]
        Normalize["L2 Normalize<br/>(after truncation)"]
        Store["pgvector<br/>HNSW Upsert"]
    end

    subgraph Query["RAG Query"]
        Q["Query Embedding"]
        Search["HNSW Similarity<br/>Search"]
        Rerank["Top-K Retrieval<br/>+ Context Assembly"]
    end

    Upload --> Parse --> Chunk --> Embed --> Normalize --> Store
    Q --> Search --> Rerank
    Store -.-> Search
```

## 4. SSE Streaming Architecture

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as FastAPI SSE
    participant L as LangGraph
    participant R as Redis Replay

    B->>F: GET /api/plans/stream
    F->>L: astream_events v2

    loop Pipeline Stages
        L->>F: run.started {run_id, seq=0}
        F->>B: SSE event
        F->>R: ZADD (score=seq)

        L->>F: stage.started {stage: "planner"}
        F->>B: SSE event
        F->>R: ZADD

        L->>F: quality.scored {score: 85}
        F->>B: SSE event
        F->>R: ZADD

        L->>F: stage.completed
        F->>B: SSE event
        F->>R: ZADD
    end

    L->>F: run.completed {run_id, seq=N}
    F->>B: SSE terminal event
    F->>R: ZADD + TTL 30min

    Note over B,R: On reconnect: GET /api/plans/{run_id}/replay?after_seq=X
    B->>F: Replay request
    F->>R: ZRANGEBYSCORE
    R->>F: Missed events
    F->>B: Replayed SSE events
```

## 5. Multi-LLM SmartRouter

```mermaid
graph TB
    subgraph Scoring["Weighted Complexity Scoring"]
        Tokens["Token Count<br/>weight: 0.25"]
        Structured["Structured Output<br/>weight: 0.25"]
        Tools["Tools Required<br/>weight: 0.25"]
        History["History Length<br/>weight: 0.15"]
        Intent["Intent Category<br/>weight: 0.10"]
    end

    Score["Composite Score<br/>(0.0 - 1.0)"]

    Tokens --> Score
    Structured --> Score
    Tools --> Score
    History --> Score
    Intent --> Score

    Score --> Route{{"Route Decision"}}

    Route -- "<= 0.40" --> Cheap["Cheap Tier<br/>Haiku 4.5 / GPT-4o-mini<br/>Gemini 2.5 Flash"]
    Route -- "0.41 - 0.70" --> Middle["Middle Tier<br/>Sonnet 4.5 / GPT-4o<br/>Gemini 2.5 Flash"]
    Route -- ">= 0.71" --> Primary["Primary Tier<br/>Opus 4.6 / GPT-4o<br/>Gemini 2.5 Pro"]

    subgraph Overrides["Hard Overrides"]
        HO1["tools_required -> skip cheap"]
        HO2["strict_json -> skip cheap"]
    end

    subgraph Escalation["Escalation Ladder"]
        E1["Self-repair (same model)"]
        E2["One tier up"]
        E3["Max 4-6 attempts"]
    end

    Overrides -.-> Route
    Cheap -.-> Escalation
    Middle -.-> Escalation
```

## 6. Sign Language Pipeline

```mermaid
graph LR
    subgraph Browser["Browser (Web Worker)"]
        Webcam["Webcam Feed"]
        MP["MediaPipe<br/>Hands + Pose<br/>(off main thread)"]
        TFJS["TF.js MLP<br/>Classifier"]
        Gloss["Gloss Labels<br/>(4 gestures MVP)"]
    end

    subgraph Server["Backend"]
        WSEndpoint["WebSocket<br/>/ws/accessibility/libras"]
        LLM["LLM Processing<br/>Gloss -> Sentence"]
    end

    subgraph Output["Output"]
        VLibras["VLibras Widget<br/>3D Libras Avatar<br/>(Government CDN)"]
        Response["Text Response"]
    end

    Webcam --> MP --> TFJS --> Gloss
    Gloss --> WSEndpoint --> LLM
    LLM --> Response
    Response --> VLibras
```

## 7. Docker Compose Topology

```mermaid
graph TB
    subgraph Host["Host Machine"]
        subgraph FrontendNet["Frontend Network"]
            FE["frontend<br/>Next.js 16<br/>:3000"]
            API2["api (exposed)"]
        end

        subgraph BackendNet["Backend Network"]
            API["api<br/>FastAPI + uvicorn<br/>:8000"]
            DB["db<br/>PostgreSQL 16<br/>+ pgvector 0.8<br/>:5432 (internal)"]
            RD["redis<br/>Redis 7.x Alpine<br/>:6379 (internal)"]
        end
    end

    FE -- "proxy /api/*" --> API2
    API2 --- API
    API --> DB
    API --> RD

    style DB fill:#336791,color:#fff
    style RD fill:#d82c20,color:#fff
    style API fill:#009688,color:#fff
    style FE fill:#000,color:#fff
```

## 8. Tenant Isolation Model

```mermaid
graph TB
    JWT["JWT Token<br/>(sub = teacher_id)"]
    MW["Tenant Context<br/>Middleware"]
    CV["contextvars<br/>TeacherId NewType"]

    JWT --> MW --> CV

    subgraph Repos["Repository Layer"]
        R1["All queries filtered<br/>by teacher_id"]
        R2["Composite FK<br/>lesson(teacher_id, course_id)<br/>-> course(teacher_id, id)"]
    end

    CV --> Repos

    subgraph Guards["Safety Guards"]
        G1["No teacher_id<br/>from request body"]
        G2["Cross-tenant<br/>integration tests"]
        G3["DB-level FK<br/>prevents leaks"]
    end
```
