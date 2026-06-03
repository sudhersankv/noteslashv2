-- Research Intelligence Agent — core schema
-- Run in Supabase SQL Editor or via CLI after 001_enable_pgvector.sql

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.transcripts (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  filename text,
  raw_text text not null,
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'ready', 'failed')),
  created_at timestamptz not null default now()
);

create table if not exists public.chunks (
  id uuid primary key default gen_random_uuid(),
  transcript_id uuid not null references public.transcripts (id) on delete cascade,
  project_id uuid not null references public.projects (id) on delete cascade,
  chunk_index int not null,
  text text not null,
  speaker text,
  start_offset int,
  end_offset int,
  embedding vector(1536),
  created_at timestamptz not null default now()
);

create index if not exists chunks_project_id_idx on public.chunks (project_id);
create index if not exists chunks_transcript_id_idx on public.chunks (transcript_id);

-- IVFFlat index: create after loading data (see supabase/README.md)
-- create index chunks_embedding_idx on public.chunks
--   using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists public.insights (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  type text not null
    check (type in ('theme', 'pain_point', 'feature_request', 'contradiction')),
  title text not null,
  description text,
  frequency int,
  confidence numeric(5, 2),
  evidence jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  markdown text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.eval_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  metrics jsonb not null default '{}'::jsonb,
  unsupported_items jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

-- Semantic search RPC (call from backend with query embedding)
create or replace function public.match_chunks(
  query_embedding vector(1536),
  match_count int,
  filter_project_id uuid
)
returns table (
  id uuid,
  transcript_id uuid,
  text text,
  speaker text,
  similarity float
)
language sql stable
as $$
  select
    c.id,
    c.transcript_id,
    c.text,
    c.speaker,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.chunks c
  where c.project_id = filter_project_id
    and c.embedding is not null
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
