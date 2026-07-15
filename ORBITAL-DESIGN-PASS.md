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

## 14. Cross-device tracking sync (operations-doc wishlist #4 — done)

Saves, dismissals, "I Applied" history, and their metadata/timestamps now sync
through a single-row `user_state` table in Supabase, so your phone and laptop
finally show the same checkmarks.

- **Model:** one row keyed `tracking`, whole-payload last-write-wins by
  timestamp. A device only adopts the remote copy when it's strictly newer
  than its own last sync; the first device to sync seeds the table with its
  existing history. Pushes are debounced (1.2s) after every save / dismiss /
  applied toggle; pulls happen at boot and on owner unlock — so unlocking on
  a brand-new device inherits everything.
- **Privacy:** owner-only in BOTH directions. Guests never read your
  tracking (verified: with owner data on the server, a guest session loads
  zero items), never write (zero server writes observed), and don't even see
  the sync indicator.
- **Honest tradeoff, stated in the SQL:** the site ships only the public
  anon key, so `user_state` grants anon INSERT/UPDATE **on itself only** —
  the jobs table stays read-only to anon, and no DELETE is granted. Someone
  who extracts the public key could scribble on one row of job-ID bookmarks;
  for a single-user tool holding no sensitive data, that's the accepted cost
  of sync without shipping the service key.
- **Graceful degradation:** no table yet / network down → status falls back
  to local-only silently, changes keep persisting to localStorage, nothing
  breaks. A live indicator in the sidebar data-status card shows
  synced / syncing / local-only / error.
- **Verified in real Chromium:** device A (localhost) saves a role → device B
  (separate origin = separate localStorage) boots fresh and inherits it with
  the indicator reading "Tracking synced across devices"; guest privacy and
  the 13-view regression all pass with zero page errors.
- **To activate:** re-run the setup SQL (it now creates `user_state`), or run
  just that block from setup.html in the Supabase SQL editor. No scraper or
  workflow changes needed.

## 15. Internships page — live instrument build-out (v6)

The page previously leaned on reference panels; in the off-season with few live
postings it read as empty. It now carries six real-data instruments, each
verified in headless Chromium on desktop and mobile (zero overflow, zero page
errors):

- **Season Timeline** — the recruiting year as a 12-month instrument band
  (primary window green, late window gold, off-cycle dim) with a computed
  "you are here" marker and a live T-minus countdown to Aug 1. Replaces the
  text-only season strip.
- **Deadline Radar** — the soonest apply-by dates from the actually loaded
  rows, as D-day countdowns (urgency-colored ≤7d / ≤21d), each row opening
  the dossier. Real parsed deadlines vs 45-day estimates are labeled
  "(est.)" per row via a single `deadlineFor()` accessor.
- **Signals Breakdown** — live percentage bars computed from the real parsed
  badges of whatever is on the board: citizenship-open vs ITAR vs clearance,
  hardware/software track, housing stipends stated, graduate-level (MS/PhD)
  eligibility.
- **Mission Prep checklist** — every line checked against actual app state
  (résumé + extracted skill count, LinkedIn URL, saved/applied internships,
  device sync status), each unmet item linking to its fix. Off-cycle months
  become runway instead of dead air.
- **My Internship Pipeline** — your own saved/applied internships with real
  applied dates, from tracking data. Renders only when it has content.
- **Early-career scope toggle** — widens the page to the codebase's native
  `earlycareer` track: real new-grad / associate / entry-level full-time
  postings previously invisible here, with a live count on the toggle.
- **Season-aware empty state** — zero postings now explains itself (off-cycle
  reality + the scope toggle + the directory) instead of a bare "no results."

**Consistency fix found along the way:** the 70% match firewall exempted
internships and early-career rows only when they were *live* — sample-mode
internships were silently gated, hiding 11 of the 17 sample internships and
making the page look emptier than the data was. Both `spaceQualifies` and
`jobsForRegion` now exempt internships and the early-career view in any data
mode, matching the codebase's own stated intent. Verified by injection test:
a new-grad row flows through scope toggle → list → radar → dossier.

## 16. Internship scan window widened to 9 months (270 days)

Internships are posted roughly 9 months before the program runs, so the old
120-day archive gate was silently discarding valid, still-open postings.
Changed in one authoritative place each:

- `isArchived()` — internships now kept **270 days** (full-time stays 45d).
- `deadlineFor()` — when no real deadline is parsed from the posting, the
  labeled "(est.)" fallback for internships is now posting-date + 270d,
  matching the true application-window length, instead of +45d.
- Doc references (the audit's 120-day mentions) updated to match.

Verified in Chromium by injection: a 200-day-old internship — dead under the
old gate — renders in the list and the Deadline Radar with an honest
estimated deadline 70 days out. The scraper needed no change: it stores every
posting with its age and only ever records *real* parsed deadlines; the
window is purely a dashboard read-time policy.

## 17. Tailoring Copilot (v8)

Per-role gap analysis inside every dossier, between the REAL posting text and
your REAL extracted skills. The core engine is local and fully transparent —
every verdict traceable to a line of the posting:

- **Requirement extraction** pulls the requirement-shaped lines out of the
  actual description (capped at 14) and marks each HIT (with the specific
  skills of yours that matched, shown inline) or GAP. Matching is full-phrase
  OR distinctive-token (6+ chars, generic words like "management" stoplisted),
  so "Payload Integration" hits an "integration and test campaigns" line
  without generic-word false positives. Verified: a realistic ops posting
  scores 4/7 covered with correct per-line attributions.
- **"Adopt their language"** — domain terms the posting uses that your skills
  list doesn't, with the explicit caveat: only claim what's true.
- **Copy this analysis** exports a plain-text tailoring brief.
- **AI drafting (optional)**: 3 résumé-bullet rewrites in their terminology +
  a cover note, under a hard no-fabrication instruction. Runs through a new
  shared `aiComplete()` transport: Claude-artifact bridge when present, else
  a user-supplied Anthropic API key (stored locally only, never synced),
  else a clear inline key prompt.

**Two latent bugs fixed on the way:** the AI Re-Score feature had never
worked on the deployed site — (a) it called `window.claude.complete`, which
only exists inside Claude.ai artifacts, and (b) its button was wired in
`rewireContent`, which never sees modal content, so the click was dead. It
now runs through `aiComplete()` and the document-level delegated click
handler, same as the copilot buttons.

## 18. Follow-Up Cadence Engine (v8)

Every "I Applied" timestamp becomes a discipline: **D+7** first follow-up due,
**D+14** second touch, **D+21 silent** = flagged as ghosted so the energy gets
redeployed. All numbers derive from your real applied timestamps.

- **Cadence panel** at the top of My Applications: D+N counter per role, due
  state, a status selector (applied / responded / interview / offer /
  rejected — non-applied statuses exit the cadence), and a **"Copy follow-up
  + log"** button that puts a role-specific follow-up email on your clipboard
  and logs the touch in one click (verified: due state clears immediately).
- **Alerts integration**: due follow-ups and ghost flags surface at the TOP
  of the Alerts view in any data mode — they're your tracking data, not pool
  statistics, so they outrank and survive the sample-mode branch (which was
  found to wholesale-reassign the alert list; cadence entries now inject
  after it).
- **Synced**: `appStatus` and `followups` ride the existing cross-device
  tracking sync.

Verified end-to-end in Chromium: time-traveled applications at D+8 / D+15 /
D+22 produce the correct three due states, copy+log interpolates the real
role title and advances the cadence, status changes exit cleanly, alerts
lead with the ghost flag, and the 13-view regression passes with zero page
errors.

## 19. Mobile dense mode (v9)

Role rows on phones were ~1.5 per screen; now ~11-12. At <=720px the 7-column
job table and the .jrow cards (internships list) each become a 2-line entry:
line 1 = title (ellipsized) + match % + save/dismiss; line 2 = company +
salary. Location/reloc/planets/extra chips hidden — tap the row for the
dossier. The early-career widget gets the same 2-line grid. The dense media
block MUST remain LAST in the stylesheet (it wins the cascade over base
.dtable rules at ~line 1092). Also fixed en route: deadline math unified on
deadlineFor() everywhere (widget + featured banner + sort had stale 45-day
estimates), the dashboard widget no longer vanishes on refreshContent, and
the Jobs subtitle's stale "90 days" copy corrected. Measured in Chromium at
412x915: dtable 62px avg (12/screen), jrow 68px avg (11/screen), zero
horizontal overflow, zero page errors, 13-view regression clean.

## 20. Epic regional hero banners (v10)

Each region's hero now merges its photo backdrop with a generative neon
skyline (inline SVG, zero external assets): Space Needle + Rainier for
Seattle, downtown towers + palms for LA, Sky Tower + harbor line for NZ, and
an orbital-arc gantry composite for Global — each with edge glow, a glossy
water reflection, and the region's accent palette. Layered beneath a glassy
live-status strip (backdrop-blur chips with a gloss sheen) built for the
landing mind-flow: orient -> status -> act. Every chip is a real computed
number — live roles in the region, internships, roles posted <=48h, the next
upcoming deadline as D-x, and the current season phase — and every chip
navigates (jobs / internships) on tap. Verified across all four regions in
one Chromium pass: correct per-region skyline, real per-region counts, chip
navigation working, zero page errors.

## 21. Cinematic hero motion (v11)

The satellite and rocket read as clip art because of the MOTION, not the
shading: linear fly-across streaks, a pinwheel spin, a cartoon wobble. All
replaced with film language, pure CSS: both objects are now anchored in
composition (rule-of-thirds right side); the satellite station-keeps along a
38s shallow drift arc with a gentle attitude sway; the rocket holds a patient
14s ascent drift with a 1-degree tilt breathe and a stepped engine-burn
glow flicker; the skyline gets a 70s parallax drift; and the hero gains a
radial vignette for frame depth. prefers-reduced-motion now freezes the
objects in place instead of hiding them. Verified in one Chromium pass:
all five animation tracks applied, both objects anchored on-screen, zero
page errors.

## 22. Text-a-role sharing + mobile perfection pass (v12)

**Sharing flow, both directions verified on a simulated fresh phone:**
- Sharer: a new "Share via text / apps" button invokes the native OS share
  sheet (Web Share API) with a composed summary — title @ company, salary,
  location, and the #share link. No-API fallback copies text+link for
  pasting into any messenger.
- Recipient: tapping the texted link on a phone that has NEVER seen Orbital
  bypasses the install gate and PIN entirely and lands on a mobile-first
  read-only role page: gradient backdrop, full role dossier content, a
  sticky bottom action bar with a 48px full-width Apply button (thumb-reach,
  safe-area aware), and an "Explore Orbital" path. Dead links (role filled/
  archived since sharing) get a graceful "no longer listed" card instead of
  dumping the friend into the app.
- Honest limitation: link previews in iMessage/WhatsApp show the site's
  generic card, not per-role imagery — per-role OG tags would need
  server-side rendering, which the static-hosting architecture deliberately
  avoids.

**Platform-wide mobile hardening:** iOS zoom-on-focus killed (16px inputs),
touch-action:manipulation + tap-highlight removal on all controls,
safe-area-inset padding on bottom bars, the dossier modal becomes a
full-screen sheet on phones with a sticky 40px glass close button, and
save/dismiss buttons meet minimum touch-target sizes within the dense rows.
Verified in one Chromium pass at 412x915: fresh-device share render, dead
link, native sheet payload, zero overflow, zero errors.

## 23. Custom hero artwork + role notes/accountability (v13)

**Hero art:** the four Unsplash photo backdrops are replaced with Lisaney's
custom sci-fi skyline artwork (Seattle / Global / LA / New Zealand), converted
from ~9MB of PNG to ~4 optimized progressive JPEGs served locally from
assets/ — faster on mobile than the old remote photos. The v10 generative
skyline SVG layer is removed (the artwork IS the skyline now); the glass
status chips, cinematic satellite/rocket motion, and vignette remain layered
on top.

**Role notes:** every dossier gets an owner-only "My Notes" block — free-text
per role (recruiter names, referral status, prep, gut feel), saved with a
timestamp, synced across devices, flagged with a note marker in the cadence
list. Verified: note persists across dossier close/reopen.

**Progression auto-tracking:** every status change (and the initial
"I Applied") is timestamped into a per-role history; the full trail
(applied Jul 2 → responded Jul 9 → interview Jul 12) renders in the cadence
panel and the dossier. Synced.

**Accountability prompts:** when follow-ups are due or roles have gone
silent 21+ days, a banner asks about them at the top of every view —
"Review now" jumps to the cadence panel; "Snooze today" quiets it until
tomorrow (per device). Verified: banner appears with a due follow-up,
snooze hides it, history logs applied→responded→interview.

## 24. Static verified intern board (v14)

A hand-verified snapshot of real, currently-open space internships baked onto
the Internships page (above the strategic matrix), from a live web scan on
Jul 14 2026. Eight rows across Rocket Lab (Space Operations — the closest
public match to an MSO profile — plus Systems/Manufacturing/Mechanical),
SpaceX (Engineering / Software / Business Operations, real Greenhouse req
links), and Blue Origin (paid + housing program). Each row states who, what,
where, how to apply (real URL), and pay — tagged [posted] (on the listing,
per CA/WA transparency law), [reported] (levels.fyi/Glassdoor), or "not
posted." The panel is explicitly labeled a frozen snapshot; the live job
list and directory remain the auto-updating layer. Verified in Chromium:
8 rows, 3 posted + 5 reported pay tags, all apply links valid http(s),
star row highlighted, zero mobile overflow, zero errors.

NOTE: pay marked [reported] must be confirmed with the recruiter — it is
crowd-sourced, not from the posting. SpaceX ranges are from the live reqs.

## 25. Honest apply-button labels (v15)

The dossier apply button hard-coded "Apply on {jobSource}", and jobSource
falls back to "LinkedIn" for any job without a known ATS — so company-page
and Greenhouse links were mislabeled "Apply on LinkedIn." New applyLabel(j)
reads the ACTUAL destination URL: "Apply on LinkedIn" only when the link
truly contains linkedin.com, otherwise a neutral "Apply here" (also for
empty/# links). Verified: LinkedIn URL → "Apply on LinkedIn"; Greenhouse and
company career pages → "Apply here".

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
