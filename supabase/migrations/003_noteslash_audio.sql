-- Noteslash: audio metadata and categorization

alter table public.projects
  add column if not exists content_type text
    check (content_type is null or content_type in ('podcast', 'interview', 'audiobook', 'lecture', 'other')),
  add column if not exists tags jsonb not null default '[]'::jsonb;

alter table public.transcripts
  add column if not exists media_type text not null default 'text'
    check (media_type in ('audio', 'text')),
  add column if not exists content_type text
    check (content_type is null or content_type in ('podcast', 'interview', 'audiobook', 'lecture', 'other')),
  add column if not exists tags jsonb not null default '[]'::jsonb,
  add column if not exists title_guess text;
