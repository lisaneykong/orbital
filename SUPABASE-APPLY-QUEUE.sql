-- ORBITAL — Apply Queue + daily email log. ADDITIVE: safe to run on a live database, it
-- touches nothing that already exists. (SUPABASE-SCHEMA.sql also creates these on a clean
-- install, so you only need this file if you are NOT doing a clean install.)

-- One row per role the morning job prepared. The résumé and cover letter are stored as
-- base64 .docx so the dashboard can download them with the anon key. You change status
-- from the dashboard (ready → applied / skipped); only the Action's service key inserts.
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
  status        text default 'ready',      -- ready | applied | skipped
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
-- Same accepted tradeoff as user_state: the browser only holds the public anon key, so it
-- can read the queue and update a row's status. No insert or delete for anon.
grant select, update on public.app_queue to anon, authenticated;
grant all privileges on public.app_queue to service_role;
alter table public.app_queue disable row level security;

-- One row per day the 8am email went out, so two DST cron slots or a manual re-run can
-- never send the same day twice.
create table if not exists public.email_log (
  sent_on    date primary key,
  sent_at    timestamptz default now(),
  roles      int,
  message_id text
);
grant select on public.email_log to anon, authenticated;
grant all privileges on public.email_log to service_role;
alter table public.email_log disable row level security;

NOTIFY pgrst, 'reload schema';
