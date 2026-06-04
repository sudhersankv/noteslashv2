# Supabase setup

1. Create a project at [supabase.com/dashboard](https://supabase.com/dashboard).
2. Run migrations in **SQL Editor**, in order:
   - `migrations/001_enable_pgvector.sql`
   - `migrations/002_initial_schema.sql`
   - `migrations/003_noteslash_audio.sql`
3. Copy **Project URL** and **service_role** key into `backend/.env`.

## Vector index (optional)

After you have hundreds of chunks, add an IVFFlat index for faster search:

```sql
create index chunks_embedding_idx on public.chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

## Security

- Use the **service role** key only on the backend server.
- Enable Row Level Security and policies before any multi-user production deployment.
