# ORBITAL — Full Feature Audit &amp; Page-by-Page Design Intent

*A running record of every ask made this build, its status, and what each
page in the nav is supposed to contain and why.*

Status key: ✅ Done · 🟡 Partial/Needs follow-up · 🔗 Real link-out (honest,
not fabricated) · ⏳ Deferred/On hold

---

## PART 1 — Every Ask, Tracked

### Install / Deployment
- ✅ Move to 100% online setup (no local Python/install.bat) — deleted local-run path entirely, browser-only.
- ✅ PIN-gate on first load, wrong PIN → read-only guest.
- ✅ Futuristic sci-fi alien-console vault UI with animated satellite/rocket art.
- ✅ One-panel install (all Supabase vars at once, not spread across files).
- ✅ Résumé upload + LinkedIn URL fields in install.
- ✅ "Copy SQL & open Supabase editor" one-click button.
- ✅ SQL now upgrades old tables in place (ALTER ADD COLUMN) instead of silently no-op'ing.
- ✅ SQL grants write permission to service_role + disables RLS (fixed recurring "permission denied").
- ✅ Exact file-upload list spelled out (contents vs. folder itself) in START-HERE.
- ✅ GitHub reframed as the *core* engine, not optional automation.
- ✅ `.github` folder copy-paste fallback (create files directly on GitHub if hidden-folder drag fails).
- ✅ IONOS auto-publish workflow (`deploy.yml`) wired to GitHub secrets.
- ✅ Config baked in (`orbital-config.js`) so the hosted site works on every device without per-device re-setup.
- ✅ Final "5 secrets" launch checklist added to START-HERE.
- ✅ Autofill/password-manager hardening on the two key fields (unique names, ignore attrs, identical-key guard).
- ✅ Hard-refresh + no-cache headers on setup.html (stale cached copy fix).
- ⏳ **On hold at your request:** convert setup.html into a true screen-by-screen wizard (Next/Back stepper). Scoped, not yet built.

### Data Accuracy / Scraper
- ✅ Real per-posting apply URLs (not homepage/search fallback) — Greenhouse `absolute_url`, Lever `applyUrl`.
- ✅ Fixed wrong ATS tokens (Blue Origin, Vast, Gravitics, LeoLabs, True Anomaly, etc.) via live-verified auto-resolution.
- ✅ Full multi-ATS scraper rebuild (Greenhouse/Workday/Lever/Ashby/Amazon/custom) per your architecture doc.
- ✅ Auto-healing upsert (drops missing columns instead of failing the batch).
- ✅ Cross-source de-duplication (same role via two ATSes merges into one row).
- ✅ Concurrency/parallelization + connection pooling + Retry-After header support.
- ✅ `companies.json` — single canonical company list (was 3 duplicated lists).
- ✅ Added 9+ new real, verified startups this session (Starcloud, Kepler Communications, Turion Space, Hubble Network, Constellation Space, Mithril Technologies, E-Space, Loft Orbital, Hermeus) — each confirmed live before adding.
- ✅ Fixed CA/LA region bug — Bay Area/NorCal cities no longer miscounted as Greater LA.
- ✅ Systems Engineering roles widened into scope (was too PM/ops-narrow).
- ✅ Internship title-detection widened (co-op, fellowship, summer analyst, trainee, apprentice, practicum).
- ✅ 270-day (~9-month) archive window for internships (vs. 45-day for full-time) — postings open roughly 9 months before the program runs.
- ✅ Real internship pay/duration extraction from posting text (was always "estimate," even when real numbers were stated).
- 🟡 Ashby/Workday/Amazon company tokens — verified where checked this session; not every one of the ~50 companies has been individually re-verified in the very latest pass.

### Internship Feature (dedicated build-out)
- ✅ Own nav button / dedicated view.
- ✅ Sort by deadline (soonest) and by program start date.
- ✅ ITAR/citizenship, clearance level, degree eligibility, hardware/software track, housing stipend — all parsed from real text into badges (dossier + row chips) and real filters.
- ✅ Real program start/end dates parsed ("Summer 2026," explicit dates) with honest fallback labeling.
- ✅ "What This Does for Your Career" section — skills gained, fit to your goal, typical next role.
- ✅ Rotating Featured Internships banner.
- ✅ Fixed: intern chip showing literal "$0/hr" / "0w" when no real pay was scraped — now shows honest "(est.)" label.
- ✅ Fixed: clicking an internship from the Early-Career widget/banner did nothing (filter-state bug in `findJob`) — now always resolves by ID.

### Matching &amp; Accuracy
- ✅ Match hardwired to your real, triple-scanned résumé (skills, targeting) by default — works before any manual setup.
- ✅ Résumé upload (Settings **and** My Profile, kept in sync) auto-extracts skills on every new upload.
- ✅ Match cache persisted (survives reloads).
- ✅ Honest answer given + optional AI semantic re-score layer added (opt-in, per-role).
- ✅ Learned-preference nudge from your real save/dismiss history.
- 🟡 Core match is keyword/regex-based, not full semantic understanding — documented as a known, permanent limitation, not something "broken."

### Fabricated/Placeholder Data — Removed
- ✅ Fake Zillow listing → removed / real-link honesty.
- ✅ Static hardcoded weather comparison → real.
- ✅ Fake pipeline "applied/interview/offer" demo IDs → real "I Applied" tracking with timestamps.
- ✅ Fake scrolling news ticker → removed entirely (too noisy, per your ask).
- ✅ Static "Next Launch" countdown → live via Launch Library 2 API.
- ✅ Static "Space Industry News" list → live via Spaceflight News API.
- ✅ Fabricated Events calendar (fake dates, fake "RFP awarded" claims) → real link-outs (AIAA, SpaceNews, etc.).
- ✅ Fabricated City Culture claims (fake "Macklemore," fake festival dates) → real link-outs (official tourism/events/news sites).
- ✅ Fully dead `GLOBAL_REGIONS` fake dataset + unreachable function → deleted outright.
- ✅ "Top Hiring Companies" chart was reading a hardcoded dataset, not live rows → now tallies from actual loaded jobs.

### UI / Design
- ✅ Generative-nebula visual theme applied everywhere (hero, vault, dossier, panels, cards, loading states).
- ✅ Real animated SVG satellite + rocket art (replaced emoji) in the hero.
- ✅ Real stock/generated photography per region (Seattle, LA, NZ skylines) at full effect intensity.
- ✅ Two-color palette per region (astigmatism-conscious).
- ✅ 10 "sexy/dramatic" style enhancements (2nd accent color, typography split, HUD glass cards, lock-on hover, ticker *(later removed)*, panel wash, mobile tilt, swipe nav, scan-skeleton loading, briefing-room dossier frame).
- ✅ 10 astigmatism-accessibility enhancements (Readable Mode bar-fallback, match icon+color, bold scatter dots, etc.).
- ✅ Global font-size increase across all views + features.
- ✅ Mobile nav moved to a fixed horizontal bottom bar, single-column layout everywhere.
- ✅ Mobile hero black-space bug fixed (was unbounded height).
- ✅ Numbered pagination (30/page) + "See all roles" toggle.
- ✅ Click a bar/dot → scrolls DOWN to the actual roles (was scrolling up/nowhere).
- ✅ Last-refresh timestamp shown; Refresh button now runs a real live scrape with true per-company progress.
- ✅ Early-Career widget correctly scoped to Dashboard only (was leaking onto every page).
- ✅ Job dossier full description formatting fixed (HTML-entity/gibberish bug; ALL-CAPS no-colon headers now split correctly).
- ✅ Full job description + responsibilities built out in the dossier (parsed into headed sections).
- 🟡 "MSO — Master of Space Operations + Graduate Certificate in Systems Engineering" title correction — flagged and corrected in code; worth a final visual re-check across every mention.

### Code Health
- ✅ Full deep-scan pass: JS/Python compile-checked, SQL-schema cross-checked against every write, dead code identified and removed, no leftover references to deleted files.
- ✅ Junk/duplicate code cleanup pass (multiple rounds).
- ✅ Speed optimization pass (match caching, concurrency, connection pooling).

---

## PART 2 — Full Page-by-Page Design Intent (What Belongs Where, and Why)

| Page | What It's For | Core Content |
|---|---|---|
| **Dashboard** | Mission control — the one glance that tells you where things stand today. | Hero (region art + greeting), live launch countdown, Early-Career &amp; Internship Radar widget (dashboard-only), Top Hiring Companies (live), salary/days-on-market scatterplot (live), KPI stat cards (live counts), live space-industry news. |
| **Jobs** | The main hunting ground — every qualifying full-time role. | Filterable/sortable list (region, relocation, sort), numbered pagination + See All, real Apply links, match %, salary, days-listed. |
| **Internships** | Dedicated early-career hunting ground — different rhythm than full-time (posted further ahead, different signals matter). | Featured rotating banner, ITAR/clearance/track filters, sort by deadline or program start date, 270-day (~9-month) window, real pay when published. |
| **My Profile** | Your living identity in the system. | Photo, name/title, core skills (from résumé), profile summary, résumé upload/view/reset (synced with Settings), LinkedIn URL. |
| **Companies** | Know who's hiring before you apply. | Real company list with live open-role counts, hiring bars. |
| **My Applications** | Track exactly where every role stands — a systems-engineering "V-Model." | Requirement Analysis (saved) → Concept Design (applied, real timestamps) → Verification (interviewing) → Mission Validation (offer). |
| **Outreach** | Networking / warm-intro tooling. | LinkedIn connection + cold-email templates, copy-to-clipboard. |
| **Insights** | Deeper analytics on the market you're targeting. | Role-demand bars (live), skill-alignment breakdowns. |
| **Strategy** | Big-picture positioning — how you're approaching the search. | Archetype/fit framing, dealbreaker and relocation logic surfaced. |
| **Events** | Real-world ways to make human connections. | Honest link-outs to real conference/hiring-event calendars (AIAA, SpaceNews, etc.) — no fabricated dates. |
| **Alerts** | Should tell you what changed since you last looked. | Live-derived signal on new/expiring postings. |
| **Reports** | Summary/export view of your search performance. | KPI snapshot, exportable. |
| **Relocation** | Make moving somewhere new feel real, not abstract. | Regional weather/culture context, real city-guide/events/news link-outs (Seattle/LA/NZ), housing link-outs. |
| **Settings** | Control room for the whole account. | Supabase connection, "Save &amp; update everything," résumé upload (synced with Profile), region default, match floor, Fetch-real-jobs dial, density/theme tweaks. |

---
---

## PART 3 — Later Sessions (reconstructed from the shipped code, Sept 2026)

*Part 1 above was written mid-build and stops before the work below. This
section was rebuilt by reading `index.html` directly rather than from chat
memory, so every line names the function or view that implements it. If an ask
from those sessions isn't here, it's because nothing in the code implements it —
worth re-raising.*

### New top-level views
- ✅ **Today** (`queue`) — the "what do I do right now" console. Ranked apply-now shortlist by `priorityScore`, honest backfill when the match floor leaves fewer than three (says so rather than showing an empty panel), overdue follow-ups, and shortcuts to full ranking / degree-relevance ranking / internship intelligence.
- ✅ **Essays** (`essays`) — application-essay workbench. See below.

### Essays / application writing
- ✅ Seeded essay questions per role, drafted in her voice from résumé + capstone + ERAU coursework, ~250 words each.
- ✅ Seeded questions are always labelled as *likely, not confirmed* — real portals can't be read (CLAUDE.md honesty rule, enforced in `essayBlock`).
- ✅ Paste the real questions from an application → "Use these questions" replaces the seeded set.
- ✅ Per-answer "Draft this answer" + Save, with edited-state tracking.
- ✅ Two honesty flags surfaced per answer where relevant: *verify against your own memory*, and *fill the bracketed slot with a real reason*.
- ✅ **Pain-Letter Generator** — problem-first opener with {COMPANY}/{ROLE}/{NAME} tokens, copy-to-clipboard.
- ✅ **Portfolio Quick-Links** panel.
- ✅ Essay text boxes widened to fill the panel (were falling back to the browser's default ~20-column width).

### Per-role dossier additions
- ✅ **Paste the JD → "Analyze requirements"** — parses the Requirements/Qualifications block from a posting and scores against it.
- ✅ **AI re-score** panel per role (opt-in).
- ✅ **My Notes** per role, owner-only, with a saved-on timestamp.
- ✅ **"Not a match" reasons** captured (`recordNotMatch`) and fed back into ranking.
- ✅ Internship prep block extended to early-career full-time roles, not just internships.

### Definitions tightened (now pinned in CLAUDE.md)
- ✅ **Hot = both conditions** — posted ≤7 days AND clears the match floor (default 70%). Recency alone is "new", not hot. `isHot(j)`.
- ✅ **Early-career on-ramps** — title OR posting body says early career / new grad / recent graduate / entry level, with `seniorityOf()` still excluding senior titles. Body-only matches allow the mid-level default title. `isEarlyCareer(j)`.
- ✅ **Location tabs pre-populate** — every region lists all its roles ranked by match on load, no button click. Global pools every region at 100/page; Seattle, LA, NZ, US Other and International list everything. `showAllRoles` + the `PS` split.
- ✅ Pagination chrome now only renders on Global — a 27-role region no longer shows a "See all 27 ranked" fold.

### Ranking / scoring
- ✅ Seniority adjustment curve — lead/director/VP penalised as out of cold-application reach, intern/entry neutral.
- ✅ Match floor exemptions: internships and the early-career view bypass the 70% floor in every data mode.
- ✅ Learned-preference nudge from real save/dismiss history.
- ✅ Salary range estimation from title seniority when the posting publishes no numbers, labelled as an estimate.

### Access / interaction
- ✅ Owner vs guest roles — notes and other write surfaces are owner-only.
- ✅ `j` / `k` keyboard navigation through the role list, suppressed while typing in a field.
- ✅ Click a company in the hiring chart → filters the job list to that company.
- ✅ Planet-rank display toggle in Settings.
- ✅ Accountability bar — counts follow-ups due and roles gone silent 21+ days, with snooze.
- ✅ Mobile hardening: 16px inputs to stop iOS zoom-on-focus, safe-area insets on both nav bars, full-screen modals.

### Diagnostic / proof pages (shipped alongside the app)
- ✅ `score-proof.html`, `coverage-seattle-la.html`, `token-probe.html`, `heal-probe.html`, `tools.html` — verification surfaces for scoring, regional coverage, ATS tokens and the auto-healing upsert.

### Still open
- 🟡 Everything still marked 🟡 in Part 1 stands (ATS token re-verification, keyword-not-semantic matching, MSO title visual re-check).
- ⏳ setup.html screen-by-screen wizard — still on hold, still not built.

---

## Bottom Line

Every "why" behind every page traces back to one goal: **remove friction
between you and a real space job**, with nothing fabricated standing in the
way of a decision you can trust.
