# ORBITAL — Design Pass (Fable 5)

*What changed in this pass, why, and what was verified. Follows the project's
own rule: nothing decorative that pretends to be data, nothing fabricated.*

---

## 1. Real bugs found & fixed

- **The four filter dropdowns on Jobs were fake.** Location / Job Category /
  Experience / Salary rendered but were wired to nothing — and "Category"
  listed Engineering/Data/Product, which isn't even this project's domain.
  Replaced with three **real, wired controls**: Experience (Early-career /
  Mid / Senior, classified from actual titles), Min salary ($100K/$150K/$200K
  against `salaryValue()`), and Sort (Best match / Highest salary / Newest).
- **Listener leak:** a `keydown` handler was re-registered on *every*
  `render()`. Consolidated into one guarded global handler.
- **Broken CSS:** `.hero .clock` contained an invalid 7-digit hex
  (`#aebaccc`) shadowed by a second declaration — cleaned up.
- **Regression caught by the new test harness during this pass:** the new
  seniority filter initially shadowed an existing `seniorityOf()` used by the
  match engine, which silently NaN-poisoned every match score. Renamed to
  `jobSeniorityBand()`; verified sample mode returns the identical 92 rows
  as the pre-change build.

## 2. Typography — instrument-grade, not sci-fi-movie

- **Orbitron removed everywhere** (index + setup vault). Its geometric
  letterforms are the single biggest "AI sci-fi template" tell, and its
  near-identical 0/O glyphs work against the astigmatism-readability goal.
- New discipline: **Space Grotesk** (display), **Inter Tight** (body),
  **JetBrains Mono** for *every* telemetry numeral — stat values and clocks
  now use tabular figures, the way real flight consoles prioritize legibility
  over theatrics.

## 3. Motion — one orchestrated moment instead of twelve loops

- Hero previously ran ~12 competing animation layers. **Removed:** comet,
  3 shooting stars, light beam, scan sweep, grid pulse, HUD gloss sheen.
  **Kept:** stars, aurora, nebula, the hand-built satellite + rocket art
  (an explicit earlier request), and the HUD radar.
- **Removed the fake waveform bars** in the HUD (pure decoration — violated
  the project's own "nothing on this screen should be decoration" rule) and
  replaced with a **real 14-day posting-activity sparkline** computed from
  actual `daysOnMarket()` values.
- Added one deliberate new moment: a **staggered panel entrance** on view
  switch (340ms, 5-step stagger). Disabled under `prefers-reduced-motion`
  and in Readable Mode.
- Hero photo grading backed off from `saturate(1.35) contrast(1.18)` to a
  calmer `1.12 / 1.06`.

## 4. Emoji → drawn iconography

- All 19 emoji panel headers, the featured-internship banner, guest/push
  strips, alert icons, résumé blocks, and key buttons now use a consistent
  1.8px-stroke SVG icon set (`CICONS` + `cic()` helper, with per-use color
  override). Region flags and weather glyphs kept — those are semantic
  content, not chrome.

## 5. The signature: Command Deck (⌘K)

A command console finally has a command line. **Ctrl/⌘+K** (or the
"Command ⌘K" button in the top bar) opens a palette that fuzzy-matches:

- **Go to** — every nav view
- **Actions** — open Settings, refresh live data, toggle Readable Mode,
  switch region
- **Roles** — live search across the actual job pool (title + company),
  Enter opens the dossier

Full keyboard support: ↑↓ navigate, ↵ select, esc closes; backdrop click
closes; results grouped and capped at 14.

## 6. Keyboard flow on listings

- **j / k** walks job rows (list and table), **Enter** opens the focused
  dossier. Focus ring is visible; disabled while typing in any field.
- Global `:focus-visible` outline added — the accessibility floor the
  design was missing.

## 7. Verified

- JS compile-checked after every edit.
- Full DOM smoke test (jsdom): boots, all 13 views render, sample pool =
  92 rows (identical to pre-change build), new filters demonstrably filter
  and sort (salary sort verified against rendered values), Command Deck
  opens/searches live roles, keyboard nav highlights rows, zero emoji left
  in panel headers.

## 8. Follow-up pass (completed)

- **Type scale tokenized.** All 44 ad-hoc rem sizes (376 declarations) now
  flow through an 18-step `--fs-*` scale declared in `:root` — including the
  three `calc(… * var(--fscale))` accessibility-scaling variants. Max drift
  from any original size is 0.05rem (~1px), and every token in use is
  verified declared.
- **Radius scale tokenized.** 16 raw pixel radii collapsed onto
  `--rx / --rs / --r / --rl / --r2` (6/10/14/18/20px). 2px and 4px detail
  radii and 999px pills stay literal by design.
- **Chip family unified.** `chip`, `srcbadge`, and `rtag` now share micro
  type + `--rx` radius via the token pass; the internships stat chips became
  a real `.statchip` class (color via `--sc2` custom property) instead of a
  ~230-character inline style per chip.
- **Inline-style hotspots classed.** Every identical ×3+ inline style is
  gone: alumni-panel inputs → `.tinput` (with the focus state the inline
  version lacked), region pills → `.locbtn` / `.locbtn.on` (now driven by
  the per-region `--a3/--a` palette instead of hardcoded cyan, so the
  active pill matches the region theme), Early-Career rows → `.ecitem`
  (gaining a hover state), launch-countdown cells → `.cdcell` (digits
  upgraded to tabular JetBrains Mono to match the console numeral system),
  mission mini-labels → `.mhi .k`. Long-form inline styles ≥40 chars:
  172 → 157, with zero duplicated ones remaining.
- **Re-verified end-to-end:** compile clean, all 13 views render, boot pool
  still exactly 92 sample rows, filters/sort still work, region switching
  restyles the active pill, Command Deck still resolves actions.

## 9. Internships build-out (from the Space Ops Master Guide)

The Internships page went from a filtered list to a full intelligence hub,
with every layer honest about its data source:

- **Search box** — the requested role-title/keyword search now sits in the
  internships toolbar and filters live against title, company, location,
  and tech tags. While wiring it, a real bug surfaced and was fixed:
  **the main search box died after the first keystroke** everywhere,
  because `rewireContent()` never rebound the rebuilt input. Search now
  survives every refresh, on Jobs and Internships alike.
- **Application Season tracker** — a computed (not hardcoded) strip that
  knows today's date: PRIMARY WINDOW OPEN (Aug–Oct), LATE WINDOW
  (Nov–Jan), or OFF-CYCLE with a live countdown to Aug 1, per the guide's
  recruitment-timeline doctrine. Includes the co-op-preference note.
- **Domain-vertical filters** — the guide's three technical verticals
  (Flight Dynamics/GNC · Ground Segment & Constellation Ops · Mission
  Assurance & Systems) are now real filter chips. Each posting is
  classified by regex against its actual title, description, and tech
  tags — live counts per chip, honest zeros when nothing matches.
- **Strategic Matrix panel** — the guide's six evaluation dimensions
  (regulatory/ITAR, org typology, timelines, tech verticals, comp &
  logistics, conversion pipelines) as an accordion briefing, each
  cross-referenced to the live badges the system already parses.
- **Global Internship Directory** — all 42 organizations across 6 hubs.
  Entities covered by the daily scraper are marked **tracked**; when real
  postings are loaded right now, a **● N live** button filters the list
  above to that company. Everything else gets an honest search link-out —
  no fabricated career-page URLs, consistent with the project's core rule.
- **Elite Pipeline Fellowships** — Brooke Owens, Patti Grace Smith, Zed
  Factor, and Matthew Isakowitz, with the off-cycle timing note.
- **Bonus bug fix:** sample-data internships titled "… Intern Intern" —
  the generator tested the original title for "Intern" after already
  substituting it in. Fixed.

Verified: search round-trips (5 → 3 → 5 rows on sample data), vertical
chips toggle and clear, directory live-links set the company filter and
scroll to the list, all other views unaffected.

## 9. Mobile rendering fix (pre-existing bug, root-caused with a real browser)

The broken phone layout (content squeezed into a ~180px strip) was **not new**
— it reproduced identically on the untouched pre-design-pass build. Root
cause: when the sidebar was made "permanently icon-only," the desktop rail
rule `.app.nav-collapsed{grid-template-columns:74px 1fr !important}` was
added **later in source** than the mobile `max-width:860px` single-column
overrides. Equal specificity, both `!important` → the rail won the cascade
on phones, forcing a `74px 1fr` grid into a 412px viewport.

Fix: the entire rail ruleset is now scoped inside `@media(min-width:861px)`,
and a redundant inline `style="grid-template-columns:74px 1fr"` on the app
element was removed. Verified in headless Chromium at 412×915: single
full-width column, zero horizontal overflow; desktop 1440px keeps the 74px
rail exactly as before.

## 10. Search that actually survives typing

The filter-bar search box (and the three filter selects) were wired only in
`wire()`, which runs on full renders — but every keystroke triggers
`refreshContent()`, which rebuilds the DOM **without rebinding them**. The
search box died after one character; the selects died after any refresh.
All filter-bar controls are now bound in `rewireContent()` (runs on every
refresh), verified in-browser: type "manager" → apply Experience=Senior →
re-sort, all chaining correctly with focus and caret preserved.

## 11. Internships section — full build-out (from the Master Guide)

- **Season tracker** (computed, never hardcoded): derives the current
  recruiting phase from today's date — PRIMARY WINDOW (Aug–Oct), LATE
  WINDOW (Nov–Jan), or OFF-CYCLE with a live countdown to Aug 1 — with the
  guide's co-op guidance attached to the right phase.
- **Search box on Internships** (the view previously had none), sharing the
  global query state and the fixed rebinding.
- **Domain-vertical filters** (guide §4): Flight Dynamics/GNC, Ground
  Segment & Constellation Ops, Mission Assurance & Systems — classified by
  regex against each posting's **real title + description text**. Chip
  counts come from the same pool the list renders; zero-count chips render
  disabled instead of leading to empty results.
- **Strategic Matrix panel**: the guide's six evaluation dimensions as
  collapsible briefing cards, cross-referencing which dimensions are
  already live badges/filters in the app.
- **Global Internship Directory**: all 36 organizations across 6 hubs.
  Scraper-covered entities are marked `tracked`; when real internship rows
  are loaded, a **"● N live" button** filters the list to that company —
  and N is computed through the *actual* list pipeline (same
  region/type/match-floor gates), so the number a button promises is
  exactly what clicking it yields — verified programmatically for every
  button. Everything else gets an honest search link-out: no fabricated
  career-page URLs, per the project's core rule.
- **Elite Fellowships panel**: Brooke Owens, Patti Grace Smith, Zed Factor,
  Matthew Isakowitz, with off-cycle timing guidance.
- A directory click clears any active search/vertical (so the promised
  count is delivered), shows a ✕-company chip, and scrolls to the list.

## 12. Verification infrastructure upgrade

This session added a **real headless-Chromium harness** (npm-hosted binary
+ puppeteer-core with CDN request stubbing). Every fix above was verified
with actual rendering: computed-style checks, mobile/desktop screenshots,
and scripted interaction tests — not just compile checks.

## 13. Vertical classification moved to ingest (scraper-side)

The three domain verticals (GNC / Ground Segment / Mission Assurance) are now
classified **in `scraper.py` at scrape time**, against the FULL posting
description — before the 4,000-character storage truncation — and stored in a
new `verticals` column (comma-joined keys, e.g. `"gnc,ground"`).

- **Python classifier** (`classify_verticals`) mirrors the dashboard's
  `VERTICAL_RE` exactly; the two are cross-referenced in comments so they
  stay in sync. Unit-tested against guide-style postings including a
  negative case (marketing internship → `""`).
- **Semantics:** `""` means classification ran and matched nothing — the
  dashboard honors that and does NOT re-guess; `null`/absent (a table that
  predates the column) triggers the client-side regex fallback, so nothing
  breaks on an un-upgraded database. All five cases verified in-browser.
- **Schema:** `verticals text` added to setup.html's CREATE TABLE plus a
  one-line `alter table public.jobs add column if not exists verticals text;`
  upgrade so re-running the setup SQL genuinely upgrades an existing table.
  Until that line is run, the scraper's auto-heal upsert simply drops the
  column and continues — no failed batches.
- **To activate on the live deployment:** run the one ALTER line in the
  Supabase SQL editor (or re-run the full setup SQL), redeploy `scraper.py`
  + `index.html` + `setup.html`, then trigger a scrape. Chip counts on the
  Internships view will populate from ingest-time classification.

## Honest follow-ups (not done)

1. The remaining ~157 unique inline styles are one-off layout tweaks —
   migrating them is possible but low-payoff churn; do it opportunistically
   when touching each component.
2. The Drill Sergeant strip and hero copy were left untouched — that voice
   is a content decision, not a design defect.
3. START-HERE.html displays an illustrative schema that predates the intern
   columns (and now `verticals`) — cosmetic drift only, since the actionable
   copy-button SQL lives in setup.html and is current, but worth refreshing
   for consistency someday.
