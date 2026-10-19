-- ORBITAL // COMMAND — TELEMETRY TABLES ONLY (safe to run on a live database)
-- Extracted verbatim from SUPABASE-SCHEMA.sql lines 87-123.
-- Creates scrape_runs + scrape_progress, which return 404 PGRST205 today.
-- Contains NO drop/delete: every statement is "create table if not exists",
-- a grant, or an index. Your jobs table is not touched.
-- Paste the whole file into Supabase -> SQL Editor -> Run.
-- Expect "Success. No rows returned".

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
