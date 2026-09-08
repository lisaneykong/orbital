-- ORBITAL // COMMAND — Supabase schema
-- Extracted verbatim from setup.html's Step 1 block, so this file and the setup screen
-- cannot drift apart. Paste the whole thing into Supabase -> SQL Editor -> Run.
-- Expect "Success. No rows returned".

-- WIPES the jobs table and rebuilds it fresh to this EXACT schema.
-- Use this if a previous table was a different shape and caused "no match" / "permission denied".
drop table if exists public.jobs cascade;
create table public.jobs (
  idx             bigint generated always as identity,
  id              text primary key,
  company         text not null,
  title           text not null,
  location_hub    text,
  location        text,
  salary_range    text,
  salary_min      int,
  salary_max      int,
  intern_rate     int,
  intern_weeks    int,
  is_intern       boolean default false,
  type            text,
  match           int,
  planets         int,
  demand          int,
  posting_age     int,
  tech            text,
  clearance       text,
  relocation_flag boolean default false,
  relocation_note text,
  logo_bg         text,
  url             text,
  timestamp       timestamptz,
  description     text,
  requirements    text,
  source          text,
  status          text default 'active',
  saved           boolean default false,
  archived        boolean default false,
  itar_flag       boolean default false,
  clearance_level text,
  degree_levels   text,
  hw_sw_track     text,
  housing_stipend boolean default false,
  intern_skills   text,
  apply_deadline  timestamptz,
  program_start   timestamptz,
  verticals       text,
  created_at      timestamptz default now()
);
-- Upgrade-in-place for tables created before the verticals column existed
-- ("create table if not exists" silently no-ops on an old table — this doesn't):
alter table public.jobs add column if not exists verticals text;

-- ============ CROSS-DEVICE TRACKING (saves / dismissals / applied) ============
-- One row keyed 'tracking', last-write-wins by timestamp. HONEST TRADEOFF: the
-- browser only ships the public anon key, so this table grants anon INSERT/UPDATE
-- on itself (and ONLY itself — the jobs table stays read-only to anon). Anyone who
-- extracts the public key could scribble on this one row of job-ID bookmarks; for a
-- single-user tool holding no sensitive data, that is the accepted cost of sync
-- without shipping the service key. No DELETE granted.
create table if not exists public.user_state (
  k          text primary key,
  v          jsonb,
  updated_at timestamptz default now()
);
grant select, insert, update on public.user_state to anon, authenticated, service_role;
alter table public.user_state disable row level security;
drop policy if exists "anon read jobs" on public.jobs;
create policy "anon read jobs" on public.jobs
  for select to anon using (true);
-- GRANT table permissions — fixes "permission denied for table jobs" even with the
-- correct service_role key (the role needs an explicit grant to write).
grant usage on schema public to anon, authenticated, service_role;
grant select on public.jobs to anon, authenticated;
grant all privileges on public.jobs to service_role;
-- Single-user tool: RLS off so the service_role key can always write. (The policies
-- above are kept as belt-and-suspenders in case a future change re-enables RLS.)
alter table public.jobs disable row level security;
-- Belt & suspenders: an explicit write policy (in case the key resolves as authenticated).
drop policy if exists "service role writes" on public.jobs;
create policy "service role writes" on public.jobs
  for all to service_role using (true) with check (true);
create index if not exists jobs_hub_time_idx
  on public.jobs (location_hub, timestamp desc);

-- ============ LIVE SCRAPE PROGRESS (powers the Refresh roles button) ============
-- The browser cannot watch scraper.py run: GitHub's API only reports whole workflow
-- STEPS, so "greenhouse came back, workday is still going" has to come from the
-- scraper itself. It writes one header row per run plus one row per ATS family as
-- each finishes, and the dashboard polls these two tables while a run is in flight.
-- Read-only to anon (it is progress telemetry, not user data); only the service key
-- the Action holds can write.
create table if not exists public.scrape_runs (
  run_id        text primary key,
  started_at    timestamptz default now(),
  finished_at   timestamptz,
  status        text default 'running',   -- running | done | failed
  boards_total  int  default 0,
  boards_done   int  default 0,
  rows_upserted int  default 0,
  trigger       text,                    -- schedule | manual | dispatch
  note          text
);
create table if not exists public.scrape_progress (
  run_id      text not null,
  source      text not null,             -- greenhouse | lever | workday | ...
  boards_done int  default 0,
  boards_total int default 0,
  rows        int  default 0,
  status      text default 'running',     -- running | done | failed
  updated_at  timestamptz default now(),
  primary key (run_id, source)
);
create index if not exists scrape_runs_started_idx on public.scrape_runs (started_at desc);
grant select on public.scrape_runs, public.scrape_progress to anon, authenticated;
grant all privileges on public.scrape_runs, public.scrape_progress to service_role;
alter table public.scrape_runs     disable row level security;
alter table public.scrape_progress disable row level security;
-- Supabase's REST layer (PostgREST) caches role permissions and does NOT always pick up
-- GRANT/RLS changes immediately — this NOTIFY forces an instant cache reload so the fix
-- above takes effect right away instead of waiting for PostgREST's automatic refresh.
NOTIFY pgrst, 'reload schema';
