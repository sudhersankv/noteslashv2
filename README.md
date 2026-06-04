# Noteslash

Turn any audio into searchable, cited notes. Upload podcasts, audiobooks, interviews, or text — Noteslash transcribes, categorizes, indexes your content, and lets you **chat** or **talk** with it.

## Features

- **Audio upload** — mp3, wav, m4a, webm, ogg (transcribed via OpenAI Whisper on upload)
- **Text upload** — paste or upload `.txt`
- **Auto-categorization** — podcast, interview, audiobook, lecture, or other
- **Semantic index** — pgvector embeddings for retrieval
- **Overview** — topics, quotes, and takeaways (labels adapt by content type)
- **Chat** — multi-turn Q&A with citations
- **Voice** — full-duplex conversation via OpenAI Realtime API + library search tool
- **Report** — export markdown summary

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, TypeScript, Tailwind |
| Backend | FastAPI, Python |
| Database | Supabase Postgres + pgvector |
| AI | OpenAI Whisper, embeddings, chat, Realtime |

## Setup

### 1. Environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Required in `backend/.env`:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Optional:
- `OPENAI_REALTIME_MODEL=gpt-realtime`
- `OPENAI_WHISPER_MODEL=whisper-1`
- `MAX_AUDIO_SIZE_MB=25`

### 2. Database migrations

Run in Supabase SQL Editor, in order:

1. `supabase/migrations/001_enable_pgvector.sql`
2. `supabase/migrations/002_initial_schema.sql`
3. `supabase/migrations/003_noteslash_audio.sql`

### 3. Run locally

```bash
# Backend
cd backend
.venv\Scripts\uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

Open http://localhost:3000

### 4. Verify

```bash
cd backend
.venv\Scripts\python scripts\verify_setup.py
.venv\Scripts\pytest
```

## Usage

1. **Start a library** — upload audio or text
2. Wait for processing (transcribe → categorize → index → insights)
3. **Overview** — read summary and key points
4. **Chat** — ask questions with cited answers
5. **Voice** — click Start voice, allow mic, speak naturally
6. **Report** — generate and download markdown

## Voice requirements

- OpenAI account with **Realtime API** access
- Browser with microphone permission
- HTTPS in production (required for mic on most browsers)

## Deploy

- **Frontend:** Vercel, root `frontend`, set `NEXT_PUBLIC_API_URL`
- **Backend:** Railway/Render, root `backend`, set env vars + `CORS_ORIGINS`

## Architecture and video

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — deployment diagrams, pipelines, API map, DB schema
- **[docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)** — 3–4 min walkthrough script

## Project structure

```
backend/app/
  services/   transcription, categorization, chat, realtime, pipeline
  routes/     projects, voice
frontend/
  components/ chat-panel, voice-panel
supabase/migrations/
backend/sample-data/  text samples for "Try sample content"
```
