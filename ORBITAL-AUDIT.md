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
- ✅ 120-day archive window for internships (vs. 45-day for full-time).
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
| **Internships** | Dedicated early-career hunting ground — different rhythm than full-time (posted further ahead, different signals matter). | Featured rotating banner, ITAR/clearance/track filters, sort by deadline or program start date, 120-day window, real pay when published. |
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

## Bottom Line

Every "why" behind every page traces back to one goal: **remove friction
between you and a real space job**, with nothing fabricated standing in the
way of a decision you can trust.
