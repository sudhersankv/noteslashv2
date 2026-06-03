# Backend

FastAPI + OpenAI + Supabase (pgvector).

## Setup

```bash
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Tests

```bash
pytest
```

## Verify setup (env + Supabase + OpenAI)

```bash
python scripts/verify_setup.py
```

## Deploy (Railway / Render)

- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set all variables from `.env.example`
- `CORS_ORIGINS` must include your Vercel frontend URL
