# ORBITAL — Feature Inventory, Work in Progress, and Suggested Fixes

Build 17 · stamp `2026-09-28.1` · inventory written 2026-10-09
Live site: jobs.lisaney.com · Repo: lisaneykong/orbital

---

## 0. Prompt to paste into ChatGPT (or any other model)

> You are reviewing **Orbital**, a single-user job-search CRM for one candidate moving into the space industry. The goal is to make it as **efficient, accurate and automated** as possible. Never use fabricated data, and never let the system invent résumé facts.
>
> Below is a complete inventory: architecture, every shipped feature, work in progress, known limitations and the suggested fixes so far. Please:
> 1. Rank the 10 changes with the biggest impact on (a) how many *right* roles he sees, (b) how few minutes each application takes, and (c) how accurate the data is. For each, give effort (S/M/L), the files it touches, and the risk.
> 2. Flag anything below that is likely to break, go stale or quietly return wrong data, and say how to detect it automatically.
> 3. Propose automation that stays inside the hard constraints in Section 1. Don't suggest auto-submitting applications or writing answers he must certify as his own.
> 4. Point out features that add complexity without value and could be cut.
> 5. For your top 3, write a concrete implementation plan: data model changes, functions and workflows, and how to test each.
>
> Be specific to this stack: a static HTML/JS app on IONOS, Supabase Postgres + REST, GitHub Actions (Python scraper + Node automation), the Anthropic API for document generation, and Resend for email. Assume no paid infrastructure beyond those.

---

## 1. Hard constraints (non-negotiable)

- **No dummy or static data.** Every role, count and chart comes from live Supabase rows. If the data source fails, the app shows "No Data" with the reason. It never falls back to sample data.
- **Never invent** résumé facts, employers, titles, dates, metrics, credentials, challenges or results. Employers, titles, dates, degrees and certifications are copied from the master résumé and can never be changed by the AI.
- His space and systems engineering background is **graduate coursework, not industry experience**. It must always be described that way.
- **No auto-submitting applications.** Portals forbid bots, need logins and CAPTCHAs, and ask for certifications only he can make. Orbital prepares each application; he reviews it and submits.
- **Essay and application answers** that he must certify as his own are only ever labelled drafts for him to rewrite. Seeded essay questions are labelled as likely, not confirmed, because real portals can't be read.
- **No sales language** in generated documents: sales, quota, pipeline, revenue, prospects, deals, closed, won, account management, business development, leads, or quota percentages.

---

## 2. Architecture

| Layer | What it is |
|---|---|
| Front end | One self-contained `index.html` (~11k lines, vanilla JS, no build step) hosted on IONOS at jobs.lisaney.com. Public Supabase URL + anon key in `orbital-config.js`. |
| Database | Supabase Postgres. Tables: `jobs`, `user_state` (cross-device tracking), `scrape_runs` + `scrape_progress` (telemetry), `app_queue` (prepared applications), `email_log`. |
| Scraper | `scraper.py` running in GitHub Actions (`scrape.yml`), with the company list in `companies.json`. |
| Automation | Node scripts in `automation/`: `prepare.mjs` (auto-prepare) and `daily-email.mjs` (8 AM brief). `lib.mjs` extracts the résumé engine from index.html so there's one source of truth. |
| Deploy | `deploy.yml` publishes to IONOS over FTP on every push. `.htaccess` sets no-cache headers. |
| Edge function | `supabase/functions/trigger-scrape` lets the dashboard's Refresh button start a scrape without exposing a GitHub token. |
| AI | Anthropic API (Claude Sonnet) for tailored résumés, cover letters, AI re-scores and essay drafts. Called from the browser with a key saved in that browser, or from Actions with a repo secret. |
| Email | Resend API. |

### Daily schedule (Central time)
| Time | What runs |
|---|---|
| 6:00 AM | Scrape → upsert into `jobs` → auto-prepare hot 75%+ roles into `app_queue` |
| ~10 AM, 2 PM, 6 PM | Catch-up scrapes. They run only if there is no successful scrape yet today (checked in Supabase). If `scrape_runs` is missing they skip; if the check fails for another reason they run anyway. |
| 8:00 AM | Daily email to one@lisaney.com |

---

## 3. Shipped features

### 3.1 Data acquisition (scraper)
- Multi-ATS scraper covering **180 configured companies**:
  - Greenhouse 31, Workday 39 (21 with guessed tokens), Lever 13, Ashby 16, BambooHR 31
  - Personio 5, Welcomekit 6, Amazon 2, custom HTML 13, and a handful on Recruitee, SmartRecruiters, Breezy, Rippling, Pinpoint and Manatal
  - 15 marked `needs_route` (no working route yet), plus 12 career-page link-outs
- Real per-posting apply URLs, not career homepages.
- Auto-resolving ATS tokens, with a cache in `resolved_tokens.json` that is ignored in git.
- **Original posting date parsed per board** (`parse_posted_date`). It handles epoch times, ISO dates, "September 3, 2026" and Workday's "Posted 3 Days Ago". It never uses the scrape date or "last updated" date. Undated roles are stored with a NULL date and are never hot.
- Cross-source de-duplication: the same role on two boards becomes one row and keeps the earlier posting date.
- Auto-healing upsert: if a column is missing, it's dropped instead of failing the whole batch.
- Concurrency, connection pooling, honouring Retry-After, and retries with backoff.
- Location bucketing into Seattle, Greater LA, New Zealand, US Other and International. Roles outside these are dropped.
- Internship detection (co-op, fellowship, summer analyst, trainee and similar), plus real pay and duration pulled from the posting text.
- Parsed eligibility badges: ITAR/citizenship, clearance level, degree level, hardware/software track, housing stipend.
- Self-healing schedule: three same-day catch-up slots. Run telemetry goes to `scrape_runs` and `scrape_progress`, and failed boards are written to `failed_scrapes_log.csv`, uploaded as a run artifact.
- `diagnose` mode: a fast per-ATS and Supabase health check that writes no rows.

### 3.2 Matching and ranking
- Match score built from his real master résumé: skill keywords, target role families and seniority.
- Seniority curve: lead, director and VP roles are penalised; intern and entry-level roles are neutral.
- Learned-preference nudge from his save and dismiss history, plus "Not a match" reasons fed back into ranking.
- Optional AI re-score for a single role.
- Paste a job description → **Analyze requirements**, which scores against the requirements block.
- Salary estimates when a posting gives no pay, always labelled "(est.)".
- **Hot** = first posted ≤7 days ago **and** at least 10% match.
- **Temperature bands:** 🔥 Hot 0–7 days · Warm 8–10 · Lukewarm 11–30 · Cold 31–60.
- **Live window:** 60 days for full-time roles, 270 days for internships.
- **Early-career on-ramps:** title or posting body says early career, new grad, recent graduate or entry level. Senior titles are still excluded.

### 3.3 Views (sidebar)
| View | What it does |
|---|---|
| **Today** | A ranked shortlist of what to apply to now, overdue follow-ups, and shortcuts. |
| **Dashboard** | Hero, live launch countdown (Launch Library 2), Early-Career & Internship Radar, Top Hiring Companies (live tally), Days-on-Market vs Salary scatter (whole market, 🔥 points for hot roles), KPI cards, live space news (Spaceflight News API). |
| **Jobs** | Every qualifying full-time role, with region tabs, filters, sorting, pagination (Global 100 per page; other regions list everything), match %, salary and days listed. |
| **Internships** | Its own view: featured banner, ITAR/clearance/track filters, sort by deadline or start date, "What this does for your career". |
| **Essays** | Seeded questions labelled likely-not-confirmed, or paste the real ones. About 250-word DRAFT answers, labelled for him to rewrite. Pain-Letter generator. Portfolio quick links. |
| **My Profile** | Photo, title, skills, summary, master résumé editor, résumé library (uploaded versions used as supporting evidence), LinkedIn. |
| **Apply Queue** *(new)* | Daily progress report. Ready-to-apply cards with downloadable tailored résumé and cover letter, gap list (hard/soft/verify), application notes (deadline, salary, clearance, onsite or hybrid, form fields), safety checks, and Mark applied / Skip. Running list of all applications with CSV export. |
| **Companies** | Live open-role counts per company, and a page per company. |
| **My Applications** | Board of Interested → Applied → Interviewing → Offer, with a follow-up cadence panel (D+7, D+14, ghosted at 21+ days), status trail and follow-up email templates. |
| **Outreach** | LinkedIn and cold-email templates. |
| **Insights** | Skill demand counted from live postings, compared with his profile; scatter; role demand and top companies. |
| **Strategy** | Playbook, hiring phases, and weekly targets counted from real applications and follow-ups. |
| **Events** | Link-outs to real calendars. No invented dates. |
| **Reports** | KPI snapshot with CSV export. |
| **Relocation** | Weather, culture and housing link-outs for Seattle, LA and NZ. Accounts for the four dogs. |
| **Settings** | Supabase connection (live only), match floor, theme and readability options, browser "Fetch real jobs", owner tools. |

### 3.4 Per-role dossier
- Full description parsed into headed sections, salary, days on market (from the original posting date), temperature and eligibility badges.
- **Tailored Résumé** (.docx). Two pages, Cambria, exact job-kit layout. Built from the master résumé with up to 24 skills and 0–4 graduate projects chosen by the AI.
  - Engine rules enforce the four anchor skills, banned skills, and coursework skills only when a supporting project is on the page.
  - Post-checks flag sales words and any numbers not in the master.
- **Cover letter** (.docx). 125–150 words, same letterhead and page border, gaps stated plainly, [bracketed slots] for the reasons only he can supply.
- Notes, I Applied, save, dismiss, share link (read-only guest view), keyboard j/k.

### 3.5 Automation
- **Auto-prepare** (after each successful scrape): hot roles at 75%+ that aren't queued, applied or dismissed, up to 10 per run. Résumé and cover letter are stored in `app_queue`. It stops cleanly on an API credits error.
- **Daily email** (8 AM Central, Resend → one@lisaney.com):
  - Every role first posted in the last 24 hours, grouped by region, with match pills and 🔥 for hot.
  - The Apply Queue, and application progress (this week, total, interviewing, offers, follow-ups due).
  - A warning banner if the morning scrape didn't finish.
  - Once-a-day guard, plain-text version, and a preview mode.

### 3.6 Sync, access and install
- Owner PIN and Google sign-in. Guest mode is read-only.
- Cross-device sync of saves, dismisses, applied roles, statuses, follow-ups, notes, the master résumé and the résumé library through `user_state`.
- One-time install: `CLEAN-INSTALL.html` (6 steps), `setup.html`, `START-HERE.html`, `install-guide.html`.
- Diagnostic pages: `pipeline-probe.html`, `heal-probe.html`, `token-probe.html`, `score-proof.html`, `coverage-seattle-la.html`, `tools.html`.
- Mobile: bottom nav, safe-area insets, 16px inputs, full-screen modals.

---

## 4. In progress / not yet verified

| Item | Status |
|---|---|
| Clean install of build 17 | **Not done.** Schema reset, push, secrets, diagnose, full run. |
| Workday (39) + custom (13) boards | **Return 0 rows.** 21 Workday tokens are guesses. Needs the diagnose log to split bad tokens from an upstream failure. |
| Telemetry tables | Don't exist on the live database until the schema runs. The catch-up gate is switched off until then. |
| Apply Queue + daily email | Built, **untested end to end.** Needs `ANTHROPIC_API_KEY` (with credits) and `RESEND_API_KEY`. The Resend sender domain needs verifying, or a Resend account registered to one@lisaney.com. |
| Tailored résumé exactly two pages | Untested on live output. |
| Posting-date parser | Untested against live Workday and Amazon responses. |
| Repo cleanup | Delete the stray root `scrape.yml` and any committed `resolved_tokens.json`. Make sure `.htaccess` is published. |
| Interview-guide generator | Not built. It's in the job kit and is the third file in every application. |
| setup.html step-by-step wizard | On hold at his request. |
| Job-kit open items | Blue Origin cover letter and interview guide; numbers-and-stories worksheet; BlackSky thesis figures; $165K "lifestyle floor" to confirm; NSLS on every résumé?; ", NC" after the dba?; SoftwareOne title via Work Number; SYSE 500 specs to check against the final report; SPAC 512/515 and L'SPACE to update when finished. |

---

## 5. Known limitations

1. **Matching is keyword/regex, not semantic.** It can miss a good role worded differently, or over-score keyword noise. AI re-score is per role and opt-in.
2. **Coverage is a hand-maintained list of 180 companies.** Space employers outside it are invisible.
3. **Internship deadlines** are usually estimates (45 days after posting) unless the posting states one.
4. **Salary** is often an estimate.
5. **Region bucketing** matches city names as text, not a geocoder.
6. **Single point of failure:** Supabase. There is no offline fallback, by design (no sample data).
7. **The browser AI key** is stored per browser. The Actions key is a separate repo secret, and both draw on the same Anthropic credits.
8. **`user_state` is writable with the anon key.** This is an accepted trade-off for a single-user tool.
9. **The prepared-files queue stores .docx as base64 in Postgres.** Fine at about 10 a day, but it will grow.

---

## 6. Suggested future fixes (prioritised)

### Accuracy
1. **Fix the 0-row boards first.** Use the diagnose output to correct the 21 guessed Workday tokens, add a nightly token health check that opens a GitHub issue when a board drops to 0, and route the 15 `needs_route` companies.
2. **Semantic match layer.** Embed postings and the master résumé (pgvector in Supabase), blend cosine similarity with the keyword score, and recalibrate against his applied, interviewed and dismissed history.
3. **Requirements parser → hard-blocker banner.** Pull required years, degree and clearance from every posting at scrape time, and mark roles with two or more "walls" as don't-apply before they reach the queue.
4. **Geocoding** (cached per location string) instead of regex bucketing.
5. **Posting-date audit:** a weekly check of a sample of live postings against the stored `timestamp`, reporting any drift.

### Efficiency
6. **Interview-guide generator** as the third prepared file, following the job kit's structure.
7. **PDF output** of the résumé and cover letter in Actions (LibreOffice headless), with an automatic two-page check. Flag in the queue any résumé that isn't exactly two pages, or has an employer split across the break.
8. **One-click apply packet:** a zip of the PDFs plus a copy-paste sheet of common form answers (contact details, work authorization, links) for him to paste in himself.
9. **Status from email:** parse confirmation and rejection emails (Gmail API, opt-in) to update statuses automatically.
10. **Follow-up drafts** queued on D+7 and D+14 for him to send.

### Automation and coverage
11. **Company discovery:** monthly search of new space-sector ATS boards (Greenhouse, Lever, Ashby search pages, NASA SBIR awardees, Space Capital portfolio lists), proposed for him to approve before they're added.
12. **Instant hot alert:** an extra email or push (ntfy or Pushover) when a 90%+ hot role lands mid-day, not only at 8 AM.
13. **Weekly report email** on Sunday: applications, response rate by role family, and time from posting to application.
14. **Store prepared files in Supabase Storage** instead of base64 columns.

### Reliability
15. **Automated smoke test** after every deploy: a headless browser loads jobs.lisaney.com, checks the build stamp, counts rows, and checks for console errors.
16. **Cost guard:** a daily cap on API spend, shown in the progress report.

---

## 7. File map

| File | Purpose |
|---|---|
| `index.html` | The whole app |
| `scraper.py`, `companies.json`, `requirements.txt` | Scraper |
| `automation/*.mjs`, `automation/package.json` | Auto-prepare + daily email |
| `.github/workflows/scrape.yml` · `daily-email.yml` · `deploy.yml` | Schedules |
| `SUPABASE-SCHEMA.sql` · `SUPABASE-APPLY-QUEUE.sql` · `SUPABASE-TELEMETRY-ONLY.sql` | Database |
| `supabase/functions/trigger-scrape/index.ts` | Refresh-button relay |
| `orbital-config.js`, `config.example.json`, `version.json`, `.htaccess`, `manifest.json` | Config / hosting |
| `CLEAN-INSTALL.html`, `setup.html`, `START-HERE.html`, `install-guide.html` | Install |
| `*-probe.html`, `score-proof.html`, `coverage-seattle-la.html`, `tools.html` | Diagnostics |
| `HANDOFF.md`, `ORBITAL-*.md`, `README.txt`, `MANIFEST.txt` | Documentation |
