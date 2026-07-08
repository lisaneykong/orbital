# ORBITAL — Operational Scheme Report

*How the system actually works end-to-end, and an honest assessment of what
could be better.*

---

## 1. The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1 — DATA ACQUISITION (runs in the cloud)          │
│  scraper.py on GitHub Actions (daily, scheduled)         │
│  + in-browser "Fetch real jobs" (instant, manual)        │
└───────────────────────┬───────────────────────────────────┘
                         │ writes rows
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2 — STORAGE (Supabase Postgres)                   │
│  one table: `jobs` — the single source of truth          │
└───────────────────────┬───────────────────────────────────┘
                         │ reads rows (anon key, read-only)
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3 — PRESENTATION (index.html, hosted on IONOS)    │
│  matching, filtering, dossiers, tracking — all client-side│
└─────────────────────────────────────────────────────────┘
```

Nothing runs on your computer. Layer 1 runs on GitHub's servers; Layer 2 is
Supabase's managed database; Layer 3 is a static file your browser executes.
This is why the "install" is really just *wiring three free cloud services
together*, not installing software.

---

## 2. How a Job Actually Gets From "Posted" to "In Front of You"

1. **GitHub Actions wakes up** on its daily schedule (or you press "Run
   workflow" / the in-app fetch button).
2. **`scraper.py` walks its company list** (`companies.json` — the single
   canonical list, deduplicated this session from what used to be three
   separate copies). For each company it knows which ATS they use
   (Greenhouse / Lever / Ashby / Workday / Amazon / Eightfold / Workable)
   and calls that ATS's real public API directly — never a fake homepage
   scrape.
3. **Each raw posting is normalized** into one common shape: company,
   title, location → mapped to a region (Seattle / Greater LA / New
   Zealand / Global), a real direct apply URL (tracking params stripped),
   a résumé-alignment score, and — for internships — parsed signals (ITAR,
   clearance, degree level, hardware/software track, real pay if stated,
   program dates).
4. **De-duplication runs twice**: once by exact ID, once by a fuzzy
   "company + normalized title + region" fingerprint, so the same role
   posted to two different ATSes doesn't show up twice.
5. **Rows are upserted into Supabase** using the service_role key (the only
   key allowed to write). If the live table is missing a column the code
   expects (e.g., an older schema), the upsert auto-heals by dropping just
   that column and retrying — so a partially-upgraded table still works.
6. **The website reads with the anon key** (read-only, safe to expose
   publicly) and pulls every row for the region/track you're viewing.
7. **Client-side, in your browser**: the match engine re-scores each role
   against your *live* résumé skills, filters (region, relocation,
   dealbreakers, ITAR/clearance), sorts (match, deadline, freshness,
   salary), paginates (30/page or See All), and renders the dossier with
   the full parsed description on click.
8. **Every interaction you take** — save, dismiss, "I Applied," résumé
   upload — writes back to `localStorage` on your device (not the shared
   database), so your personal tracking stays private and instant, with no
   network round-trip.

---

## 3. Where "Live" vs. "Computed" vs. "Linked" Actually Splits

Being precise about this matters, because "live" gets used loosely:

- **Genuinely live, pulled fresh each load:** job listings, match scores,
  hiring-company chart, salary/days-on-market scatterplot, next-launch
  countdown (Launch Library 2 API), space-industry news (Spaceflight News
  API).
- **Computed from real data, not fetched externally:** match %, dealbreaker
  flags, internship signal badges, "What This Does for Your Career" text —
  all derived by parsing the real scraped description text with regex/
  keyword logic, not a separate live feed.
- **Real, but link-out rather than embedded:** Events, City Culture,
  housing — these point to real official sources (AIAA, city tourism
  sites, Zillow) rather than showing fabricated data inline, because doing
  it properly would require paid third-party APIs.
- **Local, not shared:** saved jobs, dismissed jobs, applied tracking,
  résumé file, LinkedIn URL — all in your browser's `localStorage`, tied to
  *this device* unless you're using the baked-in `orbital-config.js` keys
  (which make the *data* universal across devices — your personal
  saves/applies are still per-device).

---

## 4. What Could Be Better (Honest List)

1. **Match scoring is keyword/regex-based, not semantic.** It's
   transparent and traceable, but it can miss a great-fit role phrased
   differently than your résumé, or over-score a role that happens to
   contain your keywords out of context. The optional AI re-score helps
   per-role but isn't applied automatically to the whole list or baked
   into sort order.

2. **Company coverage is a hand-maintained list, not comprehensive.** Only
   ~50 companies are wired in. Any space company using SmartRecruiters,
   BreezyHR, Recruitee, or a fully custom career site is invisible to the
   scraper entirely, even if it's a perfect-fit employer. This is the
   single biggest coverage gap.

3. **Internship deadlines are usually estimates.** Most ATS postings don't
   publish a real "applications close on X" date — the shown date is a
   45-day-from-posting estimate unless the posting explicitly states a
   date, which the system does detect and prefer when present.

4. **Per-device tracking.** Your saves/dismisses/applied history live in
   browser storage. Open the site on your phone and it won't show the same
   "applied" checkmarks as your laptop unless you're disciplined about
   using one device, or we build a proper synced-tracking table in
   Supabase (straightforward, just not done yet).

5. **No true notification system.** "Alerts" surfaces signals when you
   load the page — there's no push/email/SMS ping when a great new role
   appears at 2am. That would require a backend job + a notification
   service, which is a real feature gap for genuine urgency.

6. **Salary is frequently an estimate, not a posted number.** Many
   companies simply don't publish pay. The shown range is then a
   seniority/region-based model, labeled "(est.)" — accurate as a
   heuristic, not a guarantee.

7. **The learned-preference nudge needs volume.** It adjusts scoring based
   on your save/dismiss history, but with light usage it has little signal
   to work with — it gets meaningfully better only after you've used the
   system for a while.

8. **No resume-tailoring automation per role yet.** There's a "Convert
   résumé" action, but true per-job tailored résumé generation (rewriting
   bullet points to mirror a specific posting) isn't built.

9. **Region bucketing is regex-based geography, not a geocoding API.** The
   CA/LA bug (Bay Area miscounted as Greater LA) was just fixed, but the
   underlying approach — string-matching city names — will always have
   edge cases a real geocoder wouldn't.

10. **Single point of failure on Supabase's platform health.** If Supabase
    has a capacity incident (as happened this session), writes can fail
    with confusing errors that look like a config problem but are actually
    upstream. There's no offline/cached fallback data source.

---

## 5. The Honest Bottom Line

Orbital's operational core — acquisition → storage → presentation — is
sound, real, and verified end-to-end. The system does not lie to you about
what's live versus estimated versus linked-out. Its biggest genuine
limitations are **breadth of company coverage** and **matching sophistication**
— both are solvable with more engineering time, not architectural flaws. If
you want the single highest-leverage next investment, it's #2 (expanding
verified company coverage) and #1 (a more semantic match layer) — those two
directly increase how many *right* roles you actually see.
