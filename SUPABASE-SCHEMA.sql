-- ORBITAL // COMMAND — Supabase schema. The ONLY database file you need.
-- Paste the whole thing into Supabase -> SQL Editor -> Run. Expect "Success. No rows returned".
-- Safe to run any number of times, on a new or an existing database: it creates what is
-- missing, adds any missing columns, and never deletes a row. setup.html shows the same SQL.

-- ============ JOBS (written by the daily scraper) ============
create table if not exists public.jobs (
  id text primary key
);
alter table public.jobs add column if not exists idx             bigint generated always as identity;
alter table public.jobs add column if not exists company         text;
alter table public.jobs add column if not exists title           text;
alter table public.jobs add column if not exists location_hub    text;
alter table public.jobs add column if not exists location        text;
alter table public.jobs add column if not exists salary_range    text;
alter table public.jobs add column if not exists salary_min      int;
alter table public.jobs add column if not exists salary_max      int;
alter table public.jobs add column if not exists intern_rate     int;
alter table public.jobs add column if not exists intern_weeks    int;
alter table public.jobs add column if not exists is_intern       boolean default false;
alter table public.jobs add column if not exists type            text;
alter table public.jobs add column if not exists match           int;
alter table public.jobs add column if not exists planets         int;
alter table public.jobs add column if not exists demand          int;
alter table public.jobs add column if not exists posting_age     int;
alter table public.jobs add column if not exists tech            text;
alter table public.jobs add column if not exists clearance       text;
alter table public.jobs add column if not exists relocation_flag boolean default false;
alter table public.jobs add column if not exists relocation_note text;
alter table public.jobs add column if not exists logo_bg         text;
alter table public.jobs add column if not exists url             text;
alter table public.jobs add column if not exists timestamp       timestamptz;   -- original posting date, NULL when unknown
alter table public.jobs add column if not exists last_seen       timestamptz;   -- last scrape that saw the posting
alter table public.jobs add column if not exists description     text;
alter table public.jobs add column if not exists requirements    text;
alter table public.jobs add column if not exists source          text;
alter table public.jobs add column if not exists status          text default 'active';
alter table public.jobs add column if not exists saved           boolean default false;
alter table public.jobs add column if not exists archived        boolean default false;
alter table public.jobs add column if not exists itar_flag       boolean default false;
alter table public.jobs add column if not exists clearance_level text;
alter table public.jobs add column if not exists degree_levels   text;
alter table public.jobs add column if not exists hw_sw_track     text;
alter table public.jobs add column if not exists housing_stipend boolean default false;
alter table public.jobs add column if not exists intern_skills   text;
alter table public.jobs add column if not exists apply_deadline  timestamptz;
alter table public.jobs add column if not exists program_start   timestamptz;
alter table public.jobs add column if not exists verticals       text;
alter table public.jobs add column if not exists created_at      timestamptz default now();   -- first time Orbital saw it
create index if not exists jobs_hub_time_idx on public.jobs (location_hub, timestamp desc);

-- The browser holds only the public anon key: it may READ jobs. Only the scraper's
-- service_role key writes.
grant usage on schema public to anon, authenticated, service_role;
grant select on public.jobs to anon, authenticated;
grant all privileges on public.jobs to service_role;
alter table public.jobs disable row level security;
drop policy if exists "anon read jobs" on public.jobs;
create policy "anon read jobs" on public.jobs for select to anon using (true);
drop policy if exists "service role writes" on public.jobs;
create policy "service role writes" on public.jobs for all to service_role using (true) with check (true);

-- ============ CROSS-DEVICE SYNC (saves, applications, notes, master résumé) ============
-- One row keyed 'tracking', last write wins. Trade-off: the browser only has the public
-- anon key, so anon may read and write this one table (never delete). Anyone holding the
-- key could read or overwrite it. No other table is writable this way except app_queue status.
create table if not exists public.user_state (
  k          text primary key,
  v          jsonb,
  updated_at timestamptz default now()
);
grant select, insert, update on public.user_state to anon, authenticated, service_role;
alter table public.user_state disable row level security;

-- ============ SCRAPE TELEMETRY (catch-up gate, Scrape now progress, pipeline-probe) ============
create table if not exists public.scrape_runs (
  run_id        text primary key,
  started_at    timestamptz default now(),
  finished_at   timestamptz,
  status        text default 'running',   -- running | done | failed
  boards_total  int  default 0,
  boards_done   int  default 0,
  rows_upserted int  default 0,           -- rows actually written
  trigger       text,                    -- schedule | catchup | dispatch
  note          text
);
create table if not exists public.scrape_progress (
  run_id       text not null,
  source       text not null,
  boards_done  int  default 0,
  boards_total int  default 0,
  rows         int  default 0,
  status       text default 'running',
  updated_at   timestamptz default now(),
  primary key (run_id, source)
);
create index if not exists scrape_runs_started_idx on public.scrape_runs (started_at desc);
grant select on public.scrape_runs, public.scrape_progress to anon, authenticated;
grant all privileges on public.scrape_runs, public.scrape_progress to service_role;
alter table public.scrape_runs     disable row level security;
alter table public.scrape_progress disable row level security;

-- ============ APPLY QUEUE (morning auto-prepare) + DAILY EMAIL LOG ============
create table if not exists public.app_queue (
  job_id        text primary key,
  company       text,
  title         text,
  location      text,
  location_hub  text,
  url           text,
  match         int,
  posted_at     timestamptz,
  salary_range  text,
  is_intern     boolean default false,
  status        text default 'ready',      -- ready | applied | skipped | failed
  prepared_at   timestamptz default now(),
  applied_at    timestamptz,
  updated_at    timestamptz default now(),
  resume_file   text,
  resume_b64    text,
  cover_file    text,
  cover_b64     text,
  cover_text    text,
  gaps          jsonb,
  notes         jsonb,
  checks        jsonb,
  error         text
);
create index if not exists app_queue_status_idx on public.app_queue (status, prepared_at desc);
grant select, update on public.app_queue to anon, authenticated;
grant all privileges on public.app_queue to service_role;
alter table public.app_queue disable row level security;

create table if not exists public.email_log (
  sent_on    date primary key,
  sent_at    timestamptz default now(),
  roles      int,
  message_id text
);
grant select on public.email_log to anon, authenticated;
grant all privileges on public.email_log to service_role;
alter table public.email_log disable row level security;

-- PostgREST caches permissions; this makes the changes above take effect immediately.
NOTIFY pgrst, 'reload schema';
