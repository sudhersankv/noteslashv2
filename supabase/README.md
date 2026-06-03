# Supabase setup

## 1. Create project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard).
2. New project → note **Project URL** and **service role** key (Settings → API).

## 2. Run migrations

In **SQL Editor**, run files in order:

1. `migrations/001_enable_pgvector.sql`
2. `migrations/002_initial_schema.sql`

## 3. Vector index (after first data load)

IVFFlat works best with hundreds+ rows. After seeding chunks:

```sql
create index chunks_embedding_idx on public.chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

For small demos, sequential scan is fine without this index.

## 4. Security

- Backend uses **service role** key only on the server.
- For a public demo without auth, keep RLS disabled or add policies later.
- Never expose `SUPABASE_SERVICE_ROLE_KEY` to the frontend.
