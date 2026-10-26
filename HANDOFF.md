# ORBITAL — Handoff (read this first in every new chat)

Last updated: 2026-10-19. Rebuilt from the project files after the earlier chat
history was lost. Anything that was only in that chat and not written to a file
is not in here. Add it below under "Notes from the user".

## Where things stand

- **Working copy:** `C:\Users\one\Documents\Orbital` (a local git repo; first commit is build 17 exactly as zipped).
  Stamp `2026-10-19.1`, 53 kit files. See the 2026-10-23 and 2026-10-19 entries below for what changed.
- **Repo:** `lisaneykong/orbital` on `main`. At last read the repo was on `2026-09-09.6`. Builds .7 onward have never been pushed.
- **Live site:** jobs.lisaney.com (IONOS). Settings should show `2026-10-19.1` once this build is live.
- **Install:** not done yet. Follow `CLEAN-INSTALL.html` (six steps, all safe to repeat, nothing deletes data).

## 2026-10-26 — heat levels, age fade, un-skip

- **Hot:** a role is hot if it was posted in the last 7 days (`isHot`). The old 10% match floor is gone, in
  `automation/lib.mjs` too. `heatLevel()` grades hot roles 1–5: 1, plus 1/2/3 for a 55/75/90%+ match, plus 1 if
  posted within a day, capped at 5. Colors follow the Super Saiyan forms (`HEAT_FORMS`): gold, gold with blue glow,
  amber, crimson, then pulsing cyan (still under prefers-reduced-motion). `heatFlames()` replaces the single 🔥 in
  `tempBadge`, the Apply Queue cards and the region-chart points. The legend is `heatLegendHTML()`, shown in the
  chart note and Settings.
- **Age fade:** past day 7, job rows (`.jrow`, `tr.agefade`) fade linearly with `ageFade()`, from full strength to
  0.1 at `ROLE_WINDOW_DAYS`. Hovering a row restores it. Internships and undated roles don't fade.
  `ROLE_WINDOW_DAYS` is now 45 (was 60), the user's 45-day cycle.
- **Un-skip:** the Apply Queue has a Skipped section with Restore (`aqSetStatus(id,'ready')`, which also removes
  the role from the dismissed list). Settings → Removed roles links to it.

## 2026-10-25 — recruiter finder (dossier)

Every dossier has a "Recruiter for this role" block (`recruiterDossierBlock`). No posting in the database names its
recruiter. About a third print an email, but almost all are EEO or accommodation inboxes, and LinkedIn can't be
scraped. So it shows only real things:
- Recruiting contacts the posting prints (`postingContacts`, which skips EEO, accommodation and generic inboxes).
- Recruiter initials from LinkedIn's `#LI-XX` posting tags.
- Three LinkedIn people searches: this company's recruiters for the role's family (`roleFamily`), its talent
  acquisition team, and likely hiring managers. `RECRUIT_COMPANY_ALIAS` maps e.g. Kuiper to Amazon.
- A form to save the recruiter you pick (name, exact title, LinkedIn URL, email) to the role, in
  `orbital.recruiters`, which syncs. Only the owner sees saved recruiters.

The user chose this over a paid contact-data service (Apollo or Hunter), which would still only guess. Note that
`user_state` is readable with the public key (the known trade-off), so saved recruiter details sit there too.

## 2026-10-25 — LinkedIn suggestion companies

The user's 28 LinkedIn-suggested companies: 20 were already configured and working. Added:
- **Umbra:** Workable `umbra-1` (49 open).
- **Karman Space & Defense:** new `adp` bucket (`scrape_adp`, ADP Workforce Now public career-center JSON). ADP
  caps pages at 20 whatever `$top` says, so it pages by the count returned. 264 open; a test kept 35, 26 of them in
  Mukilteo, WA.
- **L3Harris Technologies, including Aerojet Rocketdyne:** new `radancy` bucket (`scrape_radancy`, the Radancy/
  TalentBrew results endpoint). 2,239 open; a test kept 433.
- **Amazon:** the Kuiper entry is now "Project Kuiper (Amazon Leo)" and searches both "kuiper" and "amazon leo"
  (`queries`), dropping duplicates. The cap is raised from 500 to 1,200 per search. A test kept 183, 124 in Seattle.
- **Not resolvable:** Lockheed Martin (Eightfold refuses outside requests with 403, left alone), Bastion Technologies,
  SEOPS and Astro Digital (no public board). Millennium Space Systems posts on Boeing's Workday board, already
  scraped as The Boeing Company.

## 2026-10-25 — dead boards resolved

The health check found 51 of 152 boards returning nothing. Each lead was confirmed by reading back real titles and
locations, not by a token match:
- **Greenhouse:** Vast Space `vast` (moved from Ashby, 187 open), Advanced Space `advancedspace`, Quantum Space
  `quantumspacellc`, Dawn Aerospace `dawnaerospace`, Interstellar Lab `interstellarlab`.
- **Ashby:** Slingshot `slingshot-aerospace` (Greenhouse board closed), Astroscale US `astroscale-us`, and Elveo
  `elveo` (lynk.world redirects to elveo.com; Lynk Global renamed).
- **BambooHR:** ClearSpace `clearspace` and Astroscale `astroscale`, replacing the dead Personio and SmartRecruiters
  entries. SmartRecruiters: ThrustMe `thrustme`.
- **Workday:** Firefly `fireflyspace`/wd115/`Firefly` (116 open), replacing the hrmdirect page.
- **New `paylocity` bucket** (`scrape_paylocity`, reads window.pageData): Agile Space Industries.
- **Custom:** Busek and OffWorld on JazzHR (applytojob.com), Exotrail on Teamtailor.
- `scrape_icims` takes an optional `host`. GDMS's iCIMS board refuses the scraper (HTTP 405), so GDMS is in
  needs_route with the link. I did not change the user agent to get around it.
- **Moved to needs_route with reasons:** 23 BambooHR guesses with no tenant (the address redirects to bamboohr.com),
  Unseenlabs, Kinéis and Look Up Space (WelcomeKit), Morpheus, Nominal, MITRE (Phenom, no public feed), EchoStar
  (iCIMS list built by JavaScript), and 8 custom pages with no readable jobs.
- The health check's Palantir failure was a one-off read timeout on its large board; the board is fine.

## 2026-10-25 — audit: schedule and static data

- **Schedule:** GitHub started the "6am" scrape slot 3–6 hours late every day in October, and the old gate threw
  away any slot that wasn't exactly 6am. So every daily scrape was the ~2pm catch-up, after the 8am email. Scrape
  slots now start ~3am Chicago on off-peak minutes (08:17, 09:47, 11:17 UTC, plus catch-ups at 15:13, 19:13 and
  23:13). Each slot runs only if Supabase has no completed scrape for the Chicago day. Email slots moved off the hour
  as well (13:23, 14:23, 15:53, 17:53 UTC; it sends from 8am, and email_log blocks doubles).
- **Static data removed:** the hand-copied July internship board (`STATIC_INTERNS`), the hardcoded event dates
  (`EVENT_SEED`, `CJ_EVENTS`; Events now lists your own events plus the live calendars), the funding-stage tags
  (`COMPANY_TIER`), and the fixed profile-card copy (`CANDIDATE`; the card now reads `OWNER`).
- **Kept on purpose (reference, not feeds):** directories and program windows (`INTERN_DIRECTORY`, `FELLOWSHIPS`,
  `INTERN_CYCLES`), relocation figures in `REGIONS` (cost-of-living index, rent, moving costs), essay prompts,
  culture links, daily motivation lines.

## 2026-10-25 — landing chart and navigation

- **Landing:** the app opens on the Dashboard (Today is now a tab beside it). On All Regions, the salary chart
  shows only roles first posted in the last 7 days, colored by region, with one dotted cost-of-living line per
  region (`colStandard`). The list under it is "Posted This Week". Points are spread sideways within each day so
  they don't stack; the tooltip keeps the real day count.
- **Region pages:** the chart and the role list cover the last 30 days (`REGION_CHART_DAYS`). 🔥 marks roles posted
  in the last 7 days, and there is one dotted line for that region's standard.
- **Standards:** $125K (`US_COL_STANDARD`) for US Other, New Zealand and International. Seattle and LA scale it by
  the midpoint of their `REGIONS[...].reloc.col` index: Seattle $188K, LA $189K. Lines within $5K share one line
  and one label.
- **Nav:** 5 buttons (`NAV_GROUPS`): Home, Jobs, Apply, Insights, Me. Related pages show as tabs (`subTabs()`).
  `NAV` stays the full page list for deep links and the command palette. The Settings tab opens the drawer.

## 2026-10-24 — profile update, Virgin Galactic back

- **Profile:** M.S. Space Systems now ends September 2027, not August (OWNER.education, the résumé JSON,
  CRED_SCHEDULE, both essays). NPWEE now records that Lisaney is Principal Investigator and that the team chose
  their mission concept as its NASA submission (certs, résumé JSON, courseworkSentence, summary blurb).
  CRED_SCHEDULE already switches each credential from "expected" to "held" on its end date.
- **Scoring:** PI and proposal terms (principal investigator, mission concept, concept study, mission formulation,
  announcement of opportunity, pre-Phase A) now count in PROPOSAL_RE and in the scraper's RESUME_DOMAIN. Satellite,
  spacecraft and space operations, mission systems and proposal-lead titles pass the scraper's TITLE_INCLUDE.
- **Virgin Galactic:** the Workday tenant is gone. The company now uses SAP SuccessFactors at
  careers.virgingalactic.com, so there is a new `successfactors` bucket and `scrape_successfactors`. The test scrape
  read 88 postings and kept 13. It was removed from needs_route and the dead Workday entry in FP_COMPANIES.

## 2026-10-24 — 2026 space-funding list added

Of the 38 startups on the user's list (raised $20M+ in 2026), 21 were already configured and working. Added, each
verified live by its job-board API and by real titles/locations: Cowboy Space, Northwood Space, Observable Space
(Ashby), Star Catcher (Greenhouse), Kapta Space (Lever). Moved off dead Personio boards: The Exploration Company
(Ashby) and Isar Aerospace (EU Greenhouse). A test scrape kept 53 roles across the 7. The Greenhouse token `apex`
belonged to a medical practice and was removed. The funding figures were not added.

**Resolve pass (same day).** Found by reading each company's careers page:
- K2 Space → `greenhouse:k2spacecorporation` (256 open), Fortastra → `greenhouse:fortastracorporation` (13),
  Apex Space → `ashby:apex-technology-inc` (135). All three are also in FP_COMPANIES.
- Pixxel → new `darwinbox` bucket (`scrape_darwinbox`, 32 open; no description endpoint, so it scores on title).
- Skyroot → new `zohorecruit` bucket (`scrape_zohorecruit`, host `skyroot.zohorecruit.in`). The host worked
  earlier on 2026-10-24 and then timed out, even to plain curl. If diagnose keeps failing it, check the host.
- Starcloud: the Greenhouse board was closed; starcloud.com/careers now redirects to `starcloud.octbr.ai` (custom).
- D-Orbit: Factorial page (custom). `scrape_custom` gained an optional `url_pattern`. When a page has no job `<a>`
  tags, it reads matching absolute URLs from the HTML and titles them from the slug, which loses punctuation
  ("Senior Fp A Analyst").
- Stale BambooHR rows for D-Orbit and Skyroot were removed. Test scrape kept K2 31, Apex 29, Pixxel 2, D-Orbit 1,
  Starcloud 0 and Fortastra 0 (15 and 13 read; all hands-on engineering, so the relevance filter dropped them).
- Still no public board: Gilmour, Xoople, SWISSto12, ElevationSpace, UNIVITY, HyImpulse, Antaris, EnduroSat,
  Interstellar. PLD Space's Odoo portal could not be reached from here. They stay in `needs_route` or BambooHR.

## 2026-10-23 — deep pass: Workday, closed postings, install

- **Runtime sweep:** every view × 6 regions × 3 tracks (576 renders), 60 dossiers, every owner action and ~35 real
  clicks, as guest and as owner (writes blocked). Zero errors.
- **Real board check** (new diagnose, run from a laptop against the live boards on 2026-10-19): only 79 of 165
  boards listed postings. Workday 7/39, BambooHR 3/31 (27 return non-JSON, likely changed endpoint), WelcomeKit 0/6,
  Personio 1/5, custom 4/13, Greenhouse 28/31 (Apex, Slingshot, Starcloud dead), Lever 11/13.
- **Workday resolver bug:** Workday answers 422 for a wrong data center/tenant and 404 for a wrong board; the old
  resolver treated any answer as the right host. Fixed, with more data centers and board-name variants.
- **companies.json:** 10 Workday boards confirmed live by the Workday API and corrected (Northrop `ngc`, RTX
  `globalhr`, Boeing, Sierra Space, Airbus `ag`, Amentum `pae`, Aerospace Corp `aero`, Moog, Maxar → board `Vantor`,
  Axiom). 21 companies not on Workday moved to `needs_route` with the reason (Lockheed, L3Harris, ULA, Virgin
  Galactic, Intuitive Machines, BlackSky, York, Terran Orbital, Mynaric, SAIC, Peraton, Jacobs, Viasat, Iridium,
  Intelsat, SES, Kratos, BWXT, Redwire, Honeywell; Blue Canyon comes in under RTX).
- **Workday scraping:** multi-site roles ("2 Locations") were all dropped; the detail call now supplies the real
  locations. Cap raised from 400 to 2,000 postings per board; on boards over 400 only titles that can qualify get a
  detail request, so the primes fit in the run. A page error mid-board keeps the rows already read.
- **Posting dates:** a dated role keeps the earliest date ever stored for it, so "Posted 30+ Days Ago" no longer
  resets daily. **Closed postings:** new `last_seen` column; the app hides a role its company's latest scrape no
  longer returned (judged per company, 36 h grace). Undated roles age out from `created_at` (first seen).
- **Dedupe** only merges across different boards, and keeps full-time and internship apart. "Technical Fellow" is no
  longer an internship (scraper, app, setup.html). Careers-page navigation links no longer become roles.
- **Schedules:** a 6 AM slot that starts late acts as a catch-up instead of being skipped; the 8 AM email sends if
  its slot starts late (email_log still prevents doubles). Claude calls in Actions retry rate limits/overloads;
  a role that fails is saved as `failed` and retried once a day.
- **App:** Early-Career radar uses `isEarlyCareer()`; dossier "why you fit" now lists real professional skills;
  "SHE" → "HE" in the cover-letter prompt; Scrape now is owner-only.
- **Install:** `SUPABASE-SCHEMA.sql` is idempotent and never deletes (parsed OK by the PostgreSQL parser); the two
  partial SQL files are removed; setup.html's SQL box matches. `deploy.yml` publishes into `IONOS_REMOTE_PATH`
  (created if missing) or the SFTP login folder on a first install; repo variable `SITE_URL` optional.
  CLEAN-INSTALL.html rewritten as one IONOS path.

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

1. **Boards still at zero** (from the 2026-10-19 board check; rerun diagnose after install for current numbers):
   - BambooHR 27 of 31 return a non-JSON page from `/careers/list`. The endpoint has probably changed.
   - WelcomeKit 0/6 and Personio 4/5 fail (HTTP 404 / no endpoint).
   - 21 companies not on Workday now sit in `needs_route`; each needs its real ATS found.
   - Custom pages: several are JavaScript-built (no links in the HTML) or have moved (404/410).
2. **Telemetry and Apply Queue tables don't exist on the live database** until `SUPABASE-SCHEMA.sql` is run.
3. **Repo cleanup** (CLEAN-INSTALL step 4): stray top-level `scrape.yml`, the two removed SQL files, and `.htaccess`
   missing from the repo.
4. **Not done yet:** one match score everywhere (the dashboard rescores; the Apply Queue and email use the raw scraper
   score); `user_state` and `app_queue` are readable/writable with the public anon key; interview-guide generator.
5. **Known limits (by design):** keyword matching, not semantic; ~165 hand-maintained boards; internship deadlines
   are usually estimates; salaries are estimates until a posting gives pay.
6. **On hold at the user's request:** a step-by-step wizard version of `setup.html`.

## Install checks

Follow `CLEAN-INSTALL.html`. **Send back:** the diagnose log (or `failed_scrapes_log.csv`) and a screenshot of
`pipeline-probe.html` after the first full run.

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
