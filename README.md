# Noteslash

Turn any audio or text into a **searchable library** with cited answers. Upload podcasts, audiobooks, interviews, or transcripts—Noteslash transcribes, categorizes, indexes your content, and lets you explore it through **Overview**, **Chat**, **Voice**, or exported **Reports**.

## Features

- **Multi-format ingest** — mp3, wav, m4a, webm, ogg, and `.txt` (Whisper transcription on upload for audio)
- **Auto-categorization** — podcast, interview, audiobook, lecture, or other, with tags
- **Semantic search** — pgvector-backed retrieval over chunked content
- **Structured insights** — topics, quotes, and takeaways with evidence linked to source passages
- **Chat** — multi-turn Q&A with inline citations
- **Voice** — full-duplex conversation via OpenAI Realtime, grounded with a `search_library` tool
- **Reports** — one-click markdown export

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind |
| API | FastAPI, Python 3.11+ |
| Database | Supabase (Postgres + pgvector) |
| AI | OpenAI Whisper, embeddings, GPT-4.1-mini, Realtime API |

## Quick start

### Prerequisites

- Node.js 20+
- Python 3.11+
- [Supabase](https://supabase.com) project
- [OpenAI](https://platform.openai.com) API key (Realtime access required for Voice)

### 1. Clone and configure

```bash
git clone https://github.com/sudhersankv/noteslashv2.git
cd noteslashv2

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Fill in `backend/.env`:

```env
OPENAI_API_KEY=...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
CORS_ORIGINS=http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

### 2. Database

Run these in the Supabase SQL Editor, in order:

1. `supabase/migrations/001_enable_pgvector.sql`
2. `supabase/migrations/002_initial_schema.sql`
3. `supabase/migrations/003_noteslash_audio.sql`

### 3. Run locally

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 4. Verify

```bash
cd backend
python scripts/verify_setup.py
pytest
```

## Usage

1. Create a **library** and upload audio or text (or use **Try sample content** on the homepage).
2. Wait for processing: categorize → index → extract insights.
3. Use **Overview**, **Chat**, **Voice**, or **Report** tabs in the workspace.

Voice requires HTTPS in production and microphone permission in the browser.

## Deployment

| Service | Root directory | Notes |
|---------|----------------|-------|
| **Frontend** (e.g. Vercel) | `frontend` | Set `NEXT_PUBLIC_API_URL` to your API URL |
| **Backend** (e.g. Railway) | `backend` | Set env from `backend/.env.example`; `CORS_ORIGINS` = frontend URL |

Start command (Railway): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design, data flows, API reference, database schema

## Project layout

```
noteslashv2/
├── frontend/           # Next.js app
├── backend/            # FastAPI API
│   ├── app/            # routes, services, agents
│   └── sample-data/    # bundled samples for /api/projects/sample
├── supabase/migrations/
└── docs/
```

## License

MIT — see [LICENSE](LICENSE).
