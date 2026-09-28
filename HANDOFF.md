# ORBITAL — Handoff (read this first in every new chat)

Last updated: 2026-09-28. Rebuilt from the project files after the earlier chat
history was lost. Anything that was only in that chat and not written to a file
is not in here. Add it below under "Notes from the user".

## Where things stand

- **Working copy:** `build/ORBITAL-v17/` (build 17, clean-install kit, stamp `2026-09-23.1`, 47 files).
  Build 17 is build 16 with no app code changed. What's new is the install path:
  `CLEAN-INSTALL.html`, `SUPABASE-TELEMETRY-ONLY.sql`, `MANIFEST.txt`.
- **Repo:** `lisaneykong/orbital` on `main`. At last read the repo was on `2026-09-09.6`. Builds .7 onward have never been pushed.
- **Live site:** jobs.lisaney.com (IONOS). Settings should show `2026-09-28.1` once build 17 is live.
- **Clean install:** not done yet (as of 2026-09-24).

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

## Where the details live

- `README.txt`: changelog, build by build. The top section is build 17.
- `ORBITAL-AUDIT.md`: every request and its status.
- `ORBITAL-CHALLENGES.md`: past failures and their root causes.
- `ORBITAL-OPERATIONS.md`: how the system works end to end.
- `ORBITAL-DESIGN-PASS.md`: design changes.
- `/github.md`: repo sync record.
- `/CLAUDE.md`: definitions that must hold (hot job, temperature bands, live window, scrape schedule, honesty rules).

## Notes from the user

(Add anything remembered from the lost chat here.)
