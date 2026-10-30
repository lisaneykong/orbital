-- ORBITAL ROW-LEVEL SECURITY (2026-10-30)
-- Applied to the live project. Re-running is safe.
--   jobs, scrape_runs, scrape_progress : anyone may READ (job listings and scrape status are not private)
--   user_state, app_queue, email_log    : only the owner's signed-in account (one@lisaney.com)
--   writes from GitHub Actions use the service-role key, which bypasses RLS
alter table public.jobs            enable row level security;
alter table public.scrape_runs     enable row level security;
alter table public.scrape_progress enable row level security;
alter table public.user_state      enable row level security;
alter table public.app_queue       enable row level security;
alter table public.email_log       enable row level security;

drop policy if exists "anon read jobs" on public.jobs;
drop policy if exists "service role writes" on public.jobs;
drop policy if exists "read jobs" on public.jobs;
create policy "read jobs" on public.jobs for select to anon, authenticated using (true);
drop policy if exists "read scrape runs" on public.scrape_runs;
create policy "read scrape runs" on public.scrape_runs for select to anon, authenticated using (true);
drop policy if exists "read scrape progress" on public.scrape_progress;
create policy "read scrape progress" on public.scrape_progress for select to anon, authenticated using (true);

drop policy if exists "owner only" on public.user_state;
create policy "owner only" on public.user_state for all to authenticated
  using ((auth.jwt()->>'email') = 'one@lisaney.com') with check ((auth.jwt()->>'email') = 'one@lisaney.com');
drop policy if exists "owner only" on public.app_queue;
create policy "owner only" on public.app_queue for all to authenticated
  using ((auth.jwt()->>'email') = 'one@lisaney.com') with check ((auth.jwt()->>'email') = 'one@lisaney.com');
drop policy if exists "owner only" on public.email_log;
create policy "owner only" on public.email_log for select to authenticated
  using ((auth.jwt()->>'email') = 'one@lisaney.com');

-- the public key can no longer touch private tables at all
revoke all on public.user_state, public.app_queue, public.email_log from anon;
revoke insert, update, delete on public.jobs, public.scrape_runs, public.scrape_progress from anon, authenticated;
grant select, insert, update on public.user_state to authenticated;

-- Email links: the page sends the salted hash of its key; true only for an unexpired key.
create or replace function public.email_pass_ok(h text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from user_state s, jsonb_array_elements(coalesce(s.v->'keys','[]'::jsonb)) e
                 where s.k = 'emailpass' and e->>'h' = h and (e->>'exp')::timestamptz > now());
$$;
revoke all on function public.email_pass_ok(text) from public;
grant execute on function public.email_pass_ok(text) to anon, authenticated;
