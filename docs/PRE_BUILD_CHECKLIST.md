# Pre-build checklist — Noteslash

## Accounts

- [ ] Supabase project
- [ ] OpenAI API key (Whisper + Chat + Embeddings + **Realtime** access)
- [ ] Vercel / Railway for deploy (optional)

## Local environment

- [ ] `backend/.env` filled
- [ ] `frontend/.env.local` with `NEXT_PUBLIC_API_URL`
- [ ] Run migrations 001, 002, **003**
- [ ] `python scripts/verify_setup.py` passes
- [ ] `pytest` passes

## Keys

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Whisper, embeddings, chat, Realtime |
| `SUPABASE_URL` | Database |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend only |
| `OPENAI_REALTIME_MODEL` | Voice tab |

## Ready

1. Upload audio or text
2. Process library
3. Chat + Voice + Report
