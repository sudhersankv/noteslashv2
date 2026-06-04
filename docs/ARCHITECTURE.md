# Noteslash — System Architecture

Technical reference for the Noteslash platform. Repository: [github.com/sudhersankv/noteslashv2](https://github.com/sudhersankv/noteslashv2)

---

## 1. What Noteslash does (30-second pitch)

**Noteslash** turns any audio or text into a **searchable library** with **cited answers**. Upload podcasts, audiobooks, interviews, or `.txt` files → transcribe → categorize → index → explore via **Overview**, **Chat**, **Voice**, or **Report**.

Every AI answer is grounded in **real passages** stored in your database—not invented quotes.

---

## 2. Production deployment topology

```mermaid
flowchart TB
  subgraph users [Users]
    Browser[Web Browser]
  end

  subgraph frontend_host [Vercel - optional]
    NextJS[Next.js 14 App]
  end

  subgraph backend_host [Railway]
    FastAPI[FastAPI / Uvicorn]
  end

  subgraph data [Supabase Cloud]
    PG[(Postgres)]
    PGV[pgvector extension]
    PG --> PGV
  end

  subgraph openai [OpenAI API]
    Whisper[Whisper STT]
    Embed[text-embedding-3-small]
    Chat[gpt-4.1-mini]
    Realtime[Realtime API WebRTC]
  end

  Browser -->|HTTPS REST| NextJS
  NextJS -->|NEXT_PUBLIC_API_URL| FastAPI
  FastAPI -->|service role| PG
  FastAPI --> Whisper
  FastAPI --> Embed
  FastAPI --> Chat
  Browser -->|WebRTC + ephemeral token| Realtime
  FastAPI -->|client_secrets| Realtime
  Browser -->|voice/tool RAG| FastAPI
```

| Component | Technology | Role |
|-----------|------------|------|
| **Frontend** | Next.js 14, React, TypeScript, Tailwind | UI, guided flow, WebRTC voice client |
| **Backend** | FastAPI, Python 3.11+ | REST API, AI orchestration, no secrets in browser |
| **Database** | Supabase (hosted Postgres) | Projects, transcripts, chunks, vectors, insights |
| **Vector search** | pgvector + `match_chunks` RPC | Semantic retrieval (1536-dim cosine) |
| **Speech-to-text** | OpenAI Whisper (`whisper-1`) | On upload; audio bytes discarded |
| **LLM** | `gpt-4.1-mini` | Categorize, insights, chat, search, report, eval judge |
| **Voice** | OpenAI Realtime (`gpt-4o-realtime-preview`) | Full-duplex speech; RAG via `search_library` tool |

**Secrets:** `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` live only on **Railway** (backend). Frontend only has `NEXT_PUBLIC_API_URL`.

---

## 3. Logical architecture (layers)

```mermaid
flowchart LR
  subgraph presentation [Presentation Layer]
    Pages[Landing / New / Processing / Workspace]
    ChatUI[ChatPanel]
    VoiceUI[VoicePanel + microphone.ts]
    APIClient[lib/api.ts]
  end

  subgraph api [API Layer - FastAPI]
    ProjectsRouter[routes/projects.py]
    VoiceRouter[routes/voice.py]
  end

  subgraph services [Service Layer]
    Transcription[transcription.py]
    Categorization[categorization.py]
    Pipeline[pipeline.py]
    Chunking[chunking.py]
    Embedding[embedding.py]
    Retrieval[retrieval.py]
    Insights[insights.py]
    Search[search.py]
    Chat[chat.py]
    Reports[reports.py]
    Evals[evals.py]
    Realtime[realtime.py]
  end

  subgraph data_access [Data Access]
    SupabaseClient[db.py]
    OpenAIClient[embedding.py]
  end

  Pages --> APIClient
  ChatUI --> APIClient
  VoiceUI --> APIClient
  APIClient --> ProjectsRouter
  APIClient --> VoiceRouter
  ProjectsRouter --> services
  VoiceRouter --> Realtime
  VoiceRouter --> Retrieval
  services --> SupabaseClient
  services --> OpenAIClient
```

---

## 4. User journey

```mermaid
flowchart TD
  start([Open Noteslash]) --> landing[Landing Page]
  landing -->|Start a library| new[New Library - upload]
  landing -->|Try sample content| sample[POST /api/projects/sample]
  new --> upload[Upload audio or text]
  sample --> processing
  upload --> processing[Processing Page - poll status]
  processing -->|POST /process| pipeline[Backend Pipeline]
  pipeline --> workspace[Workspace Tabs]
  workspace --> overview[Overview - insights + quotes]
  workspace --> chat[Chat - multi-turn RAG]
  workspace --> voice[Voice - Realtime + search_library]
  workspace --> report[Report - markdown export]
```

| Step | Route | What happens |
|------|-------|----------------|
| 1 | `/` | Product story, 4-step guide |
| 2 | `/new` or sample CTA | Create project, upload files |
| 3 | `/project/{id}/processing` | Sync process + status polling |
| 4 | `/project/{id}` | Overview \| Chat \| Voice \| Report |

---

## 5. Upload and ingestion pipeline (core differentiator)

Audio is transcribed **at upload time** (not during `/process`). Original audio is **not stored**—only text in Postgres.

```mermaid
sequenceDiagram
  participant User
  participant FE as Next.js
  participant API as FastAPI
  participant Whisper as OpenAI Whisper
  participant DB as Supabase

  User->>FE: Drop mp3 / wav / txt
  FE->>API: POST /upload multipart
  alt Audio file
    API->>Whisper: transcribe bytes
    Whisper-->>API: raw_text
    Note over API: Discard audio bytes
  else Text file
    API->>API: UTF-8 decode
  end
  API->>DB: INSERT transcripts status=pending
  FE->>API: POST /process
  loop Each transcript
    API->>API: categorize_transcript LLM
    API->>DB: UPDATE content_type tags title_guess
    API->>API: chunk_transcript speaker-aware
    API->>Whisper: embed_texts batch
    API->>DB: INSERT chunks + vector 1536
    API->>DB: UPDATE transcript status=ready
  end
  API->>API: aggregate_project_metadata
  API->>API: extract_and_store_insights LLM
  API->>DB: INSERT insights with evidence chunk_ids
  API-->>FE: status ready
```

### Processing stages (show on processing page)

1. **Transcribing audio** — already done on upload for audio; text skips this
2. **Categorizing content** — LLM assigns `podcast | interview | audiobook | lecture | other` + tags
3. **Indexing library** — chunk + embed + pgvector
4. **Extracting insights** — themes / quotes / takeaways (prompt varies by `content_type`)

**Key files:**

| Stage | File |
|-------|------|
| Upload + Whisper | [`backend/app/routes/projects.py`](../backend/app/routes/projects.py), [`transcription.py`](../backend/app/services/transcription.py) |
| Categorize | [`categorization.py`](../backend/app/services/categorization.py) |
| Chunk | [`chunking.py`](../backend/app/services/chunking.py) |
| Embed | [`embedding.py`](../backend/app/services/embedding.py) |
| Pipeline orchestration | [`pipeline.py`](../backend/app/services/pipeline.py) |
| Insights | [`insights.py`](../backend/app/services/insights.py), [`prompts.py`](../backend/app/agents/prompts.py) |

---

## 6. Semantic search and RAG (Chat + Search)

```mermaid
sequenceDiagram
  participant User
  participant FE as ChatPanel
  participant API as FastAPI
  participant RAG as retrieval.py
  participant DB as Supabase match_chunks
  participant LLM as gpt-4.1-mini

  User->>FE: Ask question
  FE->>API: POST /chat message
  API->>DB: Load chat history
  API->>RAG: embed query + match_chunks top-k
  RAG->>DB: RPC match_chunks cosine
  DB-->>RAG: chunk rows + similarity
  API->>LLM: history + quotes JSON only
  LLM-->>API: answer + cited_chunk_ids
  API->>API: rows_to_citations verbatim text
  API->>DB: INSERT user + assistant messages
  API-->>FE: answer + citations
  FE->>User: Show answer + source quotes
```

**Citation rule:** UI displays `chunk.text` from the database—never model-paraphrased “quotes.”

| Component | File |
|-----------|------|
| Vector retrieval | [`retrieval.py`](../backend/app/services/retrieval.py) |
| Chat orchestration | [`chat.py`](../backend/app/services/chat.py) |
| Citation builder | [`citations.py`](../backend/app/services/citations.py) |
| SQL RPC | [`002_initial_schema.sql`](../supabase/migrations/002_initial_schema.sql) — `match_chunks()` |

---

## 7. Voice-to-voice (Realtime + grounded tool)

Browser connects **directly** to OpenAI via WebRTC. RAG runs on **your Railway backend** so the API key stays server-side.

```mermaid
sequenceDiagram
  participant User
  participant FE as VoicePanel
  participant API as Railway FastAPI
  participant OAI as OpenAI Realtime
  participant RAG as pgvector

  User->>FE: Start voice
  FE->>API: POST /voice/session
  API->>OAI: POST /v1/realtime/client_secrets
  OAI-->>API: ephemeral client_secret
  API-->>FE: token + model
  FE->>OAI: WebRTC SDP offer/answer
  User->>OAI: Speech audio stream
  OAI->>FE: function_call search_library
  FE->>API: POST /voice/tool query
  API->>RAG: retrieve_chunks top 5
  API-->>FE: snippets JSON
  FE->>OAI: function_call_output
  OAI->>User: Spoken response audio
```

| Piece | File |
|-------|------|
| Session creation | [`realtime.py`](../backend/app/services/realtime.py), [`voice.py`](../backend/app/routes/voice.py) |
| WebRTC client | [`voice-panel.tsx`](../frontend/components/voice-panel.tsx) |
| Mic helpers | [`microphone.ts`](../frontend/lib/microphone.ts) |

**Production note:** Microphone requires **HTTPS** (Vercel/Railway public URLs). `microphone.ts` blocks insecure contexts.

---

## 8. Database schema (ER diagram)

```mermaid
erDiagram
  projects ||--o{ transcripts : contains
  projects ||--o{ chunks : has
  projects ||--o{ insights : has
  projects ||--o{ reports : has
  projects ||--o{ eval_runs : has
  projects ||--o{ chat_messages : has
  transcripts ||--o{ chunks : split_into

  projects {
    uuid id PK
    text name
    text content_type
    jsonb tags
  }

  transcripts {
    uuid id PK
    uuid project_id FK
    text filename
    text raw_text
    text status
    text media_type
    text content_type
    jsonb tags
    text title_guess
  }

  chunks {
    uuid id PK
    uuid transcript_id FK
    uuid project_id FK
    text text
    vector embedding
  }

  insights {
    uuid id PK
    uuid project_id FK
    text type
    text title
    jsonb evidence
  }

  chat_messages {
    uuid id PK
    uuid project_id FK
    text role
    text content
    jsonb citations
  }
```

**Migrations (run in order):**

1. `001_enable_pgvector.sql`
2. `002_initial_schema.sql`
3. `003_noteslash_audio.sql` — `media_type`, `content_type`, `tags`

---

## 9. REST API map

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Liveness |
| POST | `/api/projects` | Create library |
| POST | `/api/projects/sample` | Seed 3 sample transcripts |
| POST | `/api/projects/{id}/upload` | Audio → Whisper or text; store transcript |
| POST | `/api/projects/{id}/process` | Categorize → chunk → embed → insights |
| GET | `/api/projects/{id}/status` | Poll processing state |
| GET | `/api/projects/{id}/insights` | Overview data |
| POST | `/api/projects/{id}/search` | One-shot semantic Q&A |
| POST | `/api/projects/{id}/chat` | Multi-turn chat + citations |
| GET | `/api/projects/{id}/chat` | Chat history |
| POST | `/api/projects/{id}/voice/session` | Realtime ephemeral token |
| POST | `/api/projects/{id}/voice/tool` | `search_library` for voice agent |
| POST | `/api/projects/{id}/report` | Generate markdown report |
| GET | `/api/projects/{id}/report/latest` | Last report |
| POST | `/api/projects/{id}/evaluate` | Grounding score on insights |

---

## 10. Content-type behavior (podcast vs interview)

| `content_type` | Insight prompts | UI labels (Overview) |
|----------------|-----------------|----------------------|
| `interview` | themes, pain points, feature requests | Top themes / Pain points / Feature requests |
| `podcast`, `audiobook`, `lecture`, `other` | key topics, notable quotes, takeaways | Key topics / Notable quotes / Takeaways |

Same DB enum (`theme`, `pain_point`, `feature_request`); labels adapt via [`frontend/lib/labels.ts`](../frontend/lib/labels.ts).

---

## 11. Environment variables (Railway backend)

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | Whisper, embeddings, chat, realtime |
| `SUPABASE_URL` | Yes | Database |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Server-side DB access |
| `CORS_ORIGINS` | Yes | Your Vercel/production frontend URL |
| `OPENAI_CHAT_MODEL` | No | Default `gpt-4.1-mini` |
| `OPENAI_WHISPER_MODEL` | No | Default `whisper-1` |
| `OPENAI_REALTIME_MODEL` | No | Default `gpt-4o-realtime-preview` |
| `OPENAI_TTS_VOICE` | No | Default `verse` |
| `MAX_AUDIO_SIZE_MB` | No | Default `25` |

**Frontend (Vercel):** `NEXT_PUBLIC_API_URL` = Railway public URL.

---

## 12. Repository layout

```
noteslashv2/
├── frontend/                 # Next.js app (deploy root on Vercel)
│   ├── app/                  # pages: /, /new, /project/[id], processing
│   ├── components/           # chat-panel, voice-panel, insight-card
│   └── lib/                  # api.ts, microphone.ts, labels.ts
├── backend/                  # FastAPI (deploy root on Railway)
│   ├── app/
│   │   ├── routes/           # projects.py, voice.py
│   │   ├── services/         # pipeline, transcription, chat, retrieval...
│   │   └── agents/prompts.py
│   ├── sample-data/          # bundled .txt for /sample endpoint
│   └── tests/
├── supabase/migrations/
└── docs/ARCHITECTURE.md
```

---

## 13. Design principles

1. **Media-agnostic intelligence** — same RAG stack for podcast, audiobook, or interview text.
2. **Transcribe once, discard audio** — lower storage cost; text is the source of truth.
3. **Citations from DB** — answers reference stored chunk text, not model-paraphrased quotes.
4. **Voice security** — Realtime token is ephemeral; RAG runs on the backend API.
5. **Sync processing** — suitable for small libraries; async jobs are the scale-up path.
