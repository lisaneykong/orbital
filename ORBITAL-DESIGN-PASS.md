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

## Honest follow-ups (not done in this pass)

1. The 44 distinct font sizes and ~12 border radii could collapse onto a
   token scale — mechanical, low-risk, high-consistency payoff.
2. Chip family (`chip` / `srcbadge` / `rtag` / inline statChip) could share
   one base class.
3. ~350 inline `style=""` attributes could migrate into classes.
4. The Drill Sergeant strip and hero copy were left untouched — that voice
   is a content decision, not a design defect.
