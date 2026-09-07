-- Run this once in the Supabase SQL Editor before deploying Herdwise.
create table if not exists public.cows (
  cow_id text primary key,
  name text not null,
  tag text,
  breed text,
  health text not null default 'Observation'
    check (health in ('Healthy', 'Attention', 'Observation')),
  image_url text,
  activity_level text,
  body_temp numeric,
  udder_temp numeric,
  teat1_tds numeric,
  teat2_tds numeric,
  teat3_tds numeric,
  teat4_tds numeric,
  gps_coordinates text,
  last_checked timestamptz not null default now()
);

-- Keep Row Level Security enabled. The server-side secret key used by Render
-- can read this table; do not add an unrestricted public SELECT policy.
alter table public.cows enable row level security;
