# ORBITAL — Handoff (read this first in every new chat)

Last updated: 2026-10-19. Rebuilt from the project files after the earlier chat
history was lost. Anything that was only in that chat and not written to a file
is not in here. Add it below under "Notes from the user".

## Where things stand

- **Working copy:** `C:\Users\one\Documents\Orbital` (a local git repo; first commit is build 17 exactly as zipped).
  Stamp `2026-10-19.1`, 55 kit files. See the 2026-10-19 entry below for what changed.
- **Repo:** `lisaneykong/orbital` on `main`. At last read the repo was on `2026-09-09.6`. Builds .7 onward have never been pushed.
- **Live site:** jobs.lisaney.com (IONOS). Settings should show `2026-10-19.1` once this build is live.
- **Clean install:** not done yet (as of 2026-10-19). Note: CLEAN-INSTALL.html is right that there are
  **three** workflow files (scrape, deploy, daily-email). The "two workflow files" line in the test steps below is out of date.

## 2026-10-19 — quick-win fixes (stamp `2026-10-19.1`)

- **Honest run status.** `scraper.py` counts the rows actually written. A run that scraped rows but wrote none is
  `failed` and exits 1. A partial write warns and reports the real count. The catch-up gate (`scrape.yml`) and the
  email's "scrape OK" check now also require `rows_upserted > 0`.
- **Location bucketing** (`determine_location_hub` in scraper.py, `fpHubOf` in index.html, kept identical):
  - City names match as whole words.
  - A hub city only counts when its part of the location doesn't name another state or country.
  - "New Mexico"/"New England" aren't Mexico/England. "holland" is dropped; "WA, Australia" isn't Washington.
  - A bare state code only counts after a comma or at the end, so "Remote or Hybrid" is no longer US Other.
  - Fixed: Louisville KY, Auburn AL, Everett MA, Kent OH, Redmond OR and Bellevue NE were Seattle. New Mexico and
    Indiana were International. Lancaster PA, Norwalk CT, Glendale AZ, Pasadena TX and Valencia Spain were LA.
    Wellington FL was NZ.
  - Rows already in Supabase keep their old hub until a scrape rewrites them.
- **companies.json:** K2 Space region "GREATER_LA" never mapped (rows were always dropped); now "Torrance, CA".
  Tethers Unlimited was set to "New Zealand"; it is in Bothell, WA. **Confirm this one.**
- **Relocation:** the scraper wrote `relocation_note: "-"` (2,675 of 2,910 live rows), which the app showed as a
  relocation offer on every role. The scraper now writes NULL, and the app treats "-" as none.
- **Salary:** scraped salaries are estimates. The app now reads "(est.)" from `salary_range`, labels them, draws
  them hollow on the scatter, and leaves them out of the "Median Base" card. Internships no longer use the
  full-time estimate. Live data has no posted salaries at all yet.
- **Today → Chase these:** it subtracted a date string, so it was always empty. It now uses `cadenceState()`.
- **Removed made-up content:**
  - Profile card "98% / 24 applications / 6 interviews / 2 offers" (now counted from your tracking).
  - The "Comms Radar" panel.
  - The three home listings in Relocation (cost figures now say they're typed-in reference numbers).
  - The hashed "~N alumni on staff" count and the "10× referral" claim.
  - The fake fallback launch and countdown.
  - "illustrative data" in the footer.
  - "On-site in …" in the dossier, match report and shared page.
- **Launch panel image:** Launch Library 2.3 returns `image` as an object, so the background requested `/[object Object]`.
- **Deploy:** `pipeline-probe.html` is now published.
- **Stamp** bumped on index, setup, START-HERE, install-guide, CLEAN-INSTALL and version.json. START-HERE and
  install-guide were still on `2026-09-23.1`.
- **Tested:**
  - 67 location cases pass in both copies, including Workday's "US-OH-Kent" form. 672 generated strings give
    identical answers in both.
  - A stubbed scraper run covers all-written, partly-written and none-written.
  - `loadOrbitalCore` still loads.
  - Every inline script parses.
  - The app was clicked through locally as a guest against live Supabase: Dashboard, Relocation, a dossier, and
    Today with seeded test data, which was removed afterwards.
- **Seen in live data, not fixed:**
  - `app_queue` returns 404 (the table doesn't exist).
  - 21 rows with "International" in the title are stored as internships. No code in this kit does that, so an
    older version wrote them.

## Open problems

1. **Workday and custom boards produce no rows.** That's 39 Workday boards and 13 custom boards. 21 of the Workday
   boards use guessed tokens (`unverified: true` in `companies.json`). A clean install won't fix this.
   It makes a diagnosis possible.
2. **The telemetry tables don't exist.** `scrape_runs` and `scrape_progress` return 404 PGRST205, so the scraper
   has never recorded which boards failed. The scraper's self-healing retry is also silently switched off
   until `scrape_runs` exists.
3. **Repo cleanup:**
   - A stray `scrape.yml` sits at the repo root. Delete it.
   - The repo has no `.htaccess`, so the no-cache rules never publish.
   - Check for a committed `resolved_tokens.json` and delete it if present. A stale copy pins boards to dead tokens.
4. **Known limits (by design, not bugs):**
   - Matching is keyword/regex, not semantic.
   - About 50 companies are maintained by hand.
   - Internship deadlines are usually estimates.
   - Saves, dismisses and applications are tracked per device.
5. **On hold at the user's request:** a step-by-step wizard version of `setup.html`.

## Tests to run (the clean install, in order)

Follow `CLEAN-INSTALL.html`. What each step should produce:

1. **Reset the database.** Run `SUPABASE-SCHEMA.sql` in the Supabase SQL Editor. This deletes every job row, so export a CSV first if you want to keep them. `user_state` survives.
   → "Success. No rows returned."
2. **Confirm the tables.** Table Editor should list `jobs`, `user_state`, `scrape_runs` and `scrape_progress`.
   → Four tables, and `jobs` has 0 rows.
3. **Push build 17 to GitHub.** Upload the *contents* of `ORBITAL-v17` to the repo top level. Then:
   - Delete `resolved_tokens.json` if present.
   - Make sure `.github/workflows/` holds only `scrape.yml` and `deploy.yml`.
   - Delete the stray root `scrape.yml`.
   → About 47 changed files and exactly two workflow files.
4. **Check the secrets.** `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` must be set. The service key must be the service_role key, not the anon key. The three `IONOS_FTP_*` secrets are needed for auto-publish.
5. **Publish to IONOS.** This happens automatically if the IONOS secrets are set. For a manual upload, turn on hidden files and confirm `.htaccess` arrived.
   → The live Settings page shows `2026-09-28.1`.
6. **Run diagnose.** Actions → Orbital daily scrape → Run workflow, with mode set to `diagnose`. Read the Workday lines in the log and look for one of these:
   - "no data-center subdomain answered"
   - "host answers but no board variant matched"
   - HTTP 401 / 403 / 404
   
   Download `failed-scrapes-log` if it's attached. Once diagnose looks healthy, run again with mode `full`.
   → A green run, per-family results, and a first row in `scrape_runs`.

**Send back:** the Workday log lines and/or `failed_scrapes_log.csv`. Also a screenshot of `pipeline-probe.html` after the full run.

**How to read the result:**
- **The 18 verified boards return rows and the 21 guessed ones don't:** the tokens are wrong. Fix them by hand in `companies.json`.
- **All 39 stay at zero:** the problem is upstream. Check two things. First, whether the whole Workday family fails before its loop. Second, whether rows are rejected on write by the location filter. A role only survives if it maps to Seattle, Greater LA, New Zealand or US Other.

## 2026-09-28 — résumé generator synced to the job kit (stamp `2026-09-28.1`)

Source: `uploads/Kong_JobKit/` (master.json, orbital-resume-generator.js, build-cover.js) plus the pasted thread handoff.
- Master résumé seed replaced with the kit's `master.json`: C→A→R bullets, SQL added, NX "in progress", `projectLibrary` / `skillPool` / `roleRouting`. A master saved in localStorage keeps its content and gains the three library keys.
- Layout: standard • bullet in Cambria 11pt with a real tab (the Symbol bullet is gone). Character spacing of −1 on the summary, company and title lines. Optional graduate-projects section after SKILLS.
- Tailoring: screening filter (doors and walls), "Cross-functional operations and analytics professional" opener, banned sales language, approved phrasings, and fact guards (MCAS team authorship, SPAC 512/515, Keytruda, BlackSky thesis, no ITAR/IEC 62645). 0-4 projects picked by id.
- Merge enforces the skill rules: four anchor skills always kept, banned skills dropped, business coursework skills only when a project supports them. The panel shows application notes, a sales-word and new-number check, dropped skills, and the verification statement.
- Cover letter: 125-150 words, he/him, gap stated plainly, same letterhead and page border as the résumé, signed "Warmly,".
- Profile facts: B.A. entry corrected ("Minor in Dance" removed). The essay drafts no longer say the MSO has a systems engineering specialization. Completion dates are corrected (Dec 2026 / Feb 2027 / Aug 2027).
- **Not tested in a browser with a live API key yet.** Generate one résumé and check the two-page break.
- Essay answers: kept, and labelled as drafts everywhere (the per-role editor, the dossier print, the .txt export and the essay library). Each label says to rewrite the answer in his own words before submitting. The label clears once he edits an answer.
- Not in Orbital yet: interview-guide generator.

## 2026-09-28 — live-only data (no sample or static market data)

- Removed the bundled sample job set (hand-written rows plus randomly generated fill). `JOBS` is now empty.
- Data source is forced to Live. An old "Auto" or "Sample" setting saved on a device is overridden. If Supabase fails or isn't configured, the board shows No Data with the reason and never falls back to sample rows.
- Removed hardcoded market numbers: top companies, role demand, in-demand skills, the skill-rank demand index, and a fixed 12-month postings trend. Charts are now tallied from live roles (`liveSkillDemand()`, `liveCompanyTally()`, `liveRoleDemand()`) and show No Data when empty.
- Stays static by design, because these are his real facts, not market data: the master résumé seed, credential dates, profile, and the essay draft templates. His edits sync across devices through `user_state` (`orbital.masterResume` and the others in `SYNC_LS_KEYS`), and that sync only works once the table exists.

## 2026-09-28 — Hot = originally posted within 7 days

- `HOT_DAYS` changed from 5 to 7. Temperature bands are now Hot 0-7 · Warm 8-10 · Lukewarm 11-30 · Cold 31-60.
- Age is measured from the job board's ORIGINAL posting date only:
  - The dashboard recomputes it from `jobs.timestamp` on every load. It used to read the stored `posting_age`, which froze whenever a board wasn't re-scraped.
  - Scraper bugs that made old roles look new:
    - A missing or unreadable date fell back to now(). That hit every Workday row (its dates are text like "Posted 3 Days Ago") and every Amazon row (dates like "September 3, 2026").
    - Greenhouse used `updated_at`, which changes on every edit.
    - Ashby fell back to `updatedAt`, which also changes on edits.
  - The new `parse_posted_date()` reads all of these formats. Undated roles are stored with a NULL date, show "posting date unknown", and are never hot.
  - When the same role appears on two boards, the merged row keeps the earlier posting date.
  - The browser's "Fetch real jobs" button follows the same rules (`fpPostedDate`).
- Removed the leftover sample-data day overrides (`DAY_OVERRIDE`).

## 2026-09-28 — Apply Queue (auto-prepare) + 8 AM daily email

Orbital never submits applications. It prepares them; he reviews and applies.
- `automation/prepare.mjs` runs as the `prepare` job in scrape.yml after any successful scrape:
  - Picks hot roles (first posted ≤7 days ago) at ≥75% match that are not queued, applied or dismissed. Up to 10 per run; the rest carry over.
  - Builds a tailored résumé and cover letter with the same engine as index.html (`loadOrbitalCore` cuts it out of index.html, so there is one source of truth).
  - Stores both, with gaps, notes and checks, in `app_queue`.
  - Needs the `ANTHROPIC_API_KEY` secret and API credits. Skipped with a warning if the key isn't set; stops on a credits error.
- `automation/daily-email.mjs` + `daily-email.yml`: 8:00 AM Central through Resend to one@lisaney.com.
  - Contents: every role first posted in the last 24h (by board posting date), grouped by hub, highest match first; the Apply Queue; and application progress (this week, total, interviewing, offers, follow-ups due).
  - `email_log` stops a day being sent twice.
  - Manual run modes: preview (attached to the run, not sent) or send.
- New dashboard view **Apply Queue** (`#view=apply`):
  - Daily progress report.
  - Ready-to-apply cards with résumé and cover-letter downloads, gaps, notes and checks, plus Mark applied / Skip. Mark applied mirrors into My Applications; Skip dismisses the role.
  - A running list of all applications with CSV export.
- Tables `app_queue` and `email_log` are in SUPABASE-SCHEMA.sql. `SUPABASE-APPLY-QUEUE.sql` adds them without a reset.
- Removed more fixed numbers from the Strategy view: weekly targets now count real applications and follow-ups, and no phases are pre-marked done. Outreach and networking counts were dropped because nothing tracks them.
- **Untested end to end.** Needs the clean install, both secrets, and a manual run of each workflow.
- **Resend sender:** `onboarding@resend.dev` only delivers to the email the Resend account is registered with. Either sign up to Resend with one@lisaney.com, or verify lisaney.com in Resend (DNS records in IONOS) and set EMAIL_FROM.

## Where the details live

- `ORBITAL-FEATURES.md`: full feature inventory, work in progress, and suggested fixes, with a ChatGPT review prompt at the top.
- `README.txt`: changelog, build by build. The top section is build 17.
- `ORBITAL-AUDIT.md`: every request and its status.
- `ORBITAL-CHALLENGES.md`: past failures and their root causes.
- `ORBITAL-OPERATIONS.md`: how the system works end to end.
- `ORBITAL-DESIGN-PASS.md`: design changes.
- `/github.md`: repo sync record.
- `/CLAUDE.md`: definitions that must hold (hot job, temperature bands, live window, scrape schedule, honesty rules).

## Notes from the user

(Add anything remembered from the lost chat here.)
