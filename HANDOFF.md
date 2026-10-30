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

## 2026-10-30 — Supabase locked down (row-level security)

- **RLS on every table** (`supabase/rls-lockdown.sql`, applied to the live project as migration
  `rls_lockdown_2026_10_30`). The public key can read `jobs`, `scrape_runs` and `scrape_progress` only. It can no
  longer read or write `user_state`, `app_queue` or `email_log`; those are limited to the signed-in Supabase account
  one@lisaney.com. GitHub Actions use the service-role key and are unaffected. Verified from outside: private
  tables return 42501, and writes/deletes return 401.
- **Database sign-in:** after the owner PIN, a device without a session shows "Sign this device in". It emails a
  one-time Supabase link (`signInWithOtp`, `shouldCreateUser:false`), and the device then stays signed in. Until
  then the device reads jobs only; tracking and Apply Queue stay local and sync after sign-in.
- **Email links:** the key check moved to `email_pass_ok(h)`, a SECURITY DEFINER function that returns only true or
  false for a salted hash. Supabase's linter warns that it is publicly callable; that is by design. A key opens the
  screen, but private data still needs the device to be signed in.
- **Schema scripts:** `SUPABASE-SCHEMA.sql` and setup.html now end with the lockdown block, so re-running them can't
  switch security back off.
- **If the sign-in link lands on the wrong site:** add https://jobs.lisaney.com to Supabase → Authentication → URL
  Configuration (Site URL / Redirect URLs).

## 2026-10-30 — email and auto-prepare use the dashboard's fit score; posted pay

- **New `automation/fit.mjs`** runs index.html's own `enhanceMatch`, `heatLevel`, `salaryLabel` and
  `relocationFit` in Node against the synced `user_state` tracking. The email and prepare used the scraper's raw
  `match`, so a role sold as 85% opened in the dossier at 48% (AST SpaceMobile Sr Director: seniority, 15+ years,
  Avoid Texas).
- **Daily email:** all roles posted in the last 24 h, minus skipped/applied, in two sections listed in full:
  Hot (75%+ fit, 4–5 flames) and Lukewarm (55–74%, 3 flames); weaker ones are counted only. Each row leads with
  match %, flames, title, salary (est. marked), company, location, relocation verdict and flags. Rows are compact
  because Gmail clips past ~102 KB; a 237-role day still builds to ~138 KB, so Gmail may show "View entire message".
- **prepare.mjs** selects roles at 75%+ by the same fit score.
- **enhanceMatch:** penalties now apply after the 100 cap (they used to be absorbed by headroom). Cache key bumped
  to `fit-2026-10-30-penalty-after-cap`.
- **Scraper:** `extract_posted_salary()` reads a posted pay range ("$150,000 - $190,000", "$120K–$160K",
  "USD 98,000 to 140,000") from the description; only rows without one keep the "(est.)" estimate.

## 2026-10-26 — worldwide metro scan: 28 boards, Teamtailor reader

About 200 space employers in the target metros were probed: Seattle, LA, San Diego, the Bay Area, Portland,
Boston, Chicago, Denver–Boulder, Toronto/Ottawa, Munich and Germany, Helsinki, the UK, Spain, France,
Luxembourg, Australia and New Zealand, plus the Asia list. Each board below was read back with real titles and
locations, then test-scraped through `scraper.py` before it was added.

- **US:** Outpost Space, Katalyst Space Technologies, GITAI (LA), Interlune, SEAKR Engineering, NASA JPL (Workday
  `citjpl`), Draper (Workday), Loft Federal (Loft Orbital's US government arm, a separate Greenhouse board).
- **Canada:** Telesat, NorthStar Earth & Space, Mission Control Space Services.
- **Europe:**
  - Thales Alenia Space, ArianeGroup, constellr, Hemeria, Exotrail.
  - Yuri, OKAPI:Orbits, OroraTech, Vyoma, LiveEO, Dcubed (Munich/Germany).
  - Kreios Space, Xoople (Spain); Oxford Space Systems (UK); ReOrbit (Helsinki).
- **Asia:** ispace (Tokyo/Luxembourg/Colorado), Synspective (Tokyo).

New scraper options:
- **`scrape_teamtailor()`** (bucket `teamtailor`, keyed by `host`). Reads the public `jobs.rss`, which carries the
  description, publish date and office. Many European start-ups use Teamtailor, and its keyed API was why
  earlier passes listed it as "tried".
- **Workday `loc_alias`.** JPL posts every role as "JPL Campus", which the hub classifier dropped; the alias maps it
  to Pasadena.
- **Workday `search`.** Scopes a group-wide tenant: Thales has 2,000+ postings, and "Thales Alenia Space" narrows
  them to ~317.

Fixes:
- **Outpost:** the old Ashby `outpost` entry was a freight-logistics company named Outpost, not Outpost Space. It is
  replaced by Greenhouse `outpostspace`. Two freight rows from 2026-09-21 remain in the database and age out of the
  45-day window by 2026-11-05.
- **Exotrail** moved from the custom-HTML reader (2 garbled titles) to Teamtailor (7 clean roles).

Rejected:
- **Name collisions:** Mercury (a bank), Rubicon (Sarajevo), "mda" on BambooHR, Reflex (Austin), Dark, Latitude
  (automotive), "magellan" (French IT consultancy), "myriota" on BambooHR (European roles), Pale Blue, Pangea.
- **Tested and dropped:** AeroVironment/BlueHalo kept 85 drone and EW rows in 222 s. Cubic and Epirus are not space
  employers.

68 companies with no readable board are in `needs_route` with the reason and careers URL. Examples:
- Kymeta (Jobvite) and Aurora Flight Sciences (Taleo).
- Inovor (SEEK, whose terms bar collection).
- ArkEdge (Japanese-only HERP board).
- Most of Australia, which posts on in-house pages.

**Run time:** the four new Workday boards add ~8 min of serial work, about one extra minute with 8 workers. Today's
run (2026-10-26, before these boards) took 14 min; expect ~15–16 min, against the 25-min timeout. The new boards
first appear in the 2026-10-27 run.

**Diagnose after the change:** 141 of 146 boards listed postings. The 5 misses were transient: Workable rate
limits (429) during the burst, and Anduril, Loft Orbital and Booz Allen, which all answered on a recheck minutes
later.

## 2026-10-26 — new region tabs, render speed

- **Four new tabs:** Europe, Canada, Asia and Australia (`REGIONS`, `REGION_ORDER`), each with a scenic header
  photo hot-linked from Unsplash (free Unsplash License, credited with a "Photo: Unsplash" link): Munich under the
  Alps, Toronto across Lake Ontario, Tokyo with Mount Fuji, Sydney Harbour. They are views of International: a role
  keeps `region:'intl'` and `intlZone()` places it, and `inRegion()` is used by `jobsForRegion`, `regionPool` (stat
  cards) and the list filter. Each tab has its own heat-map view, hero colors, live weather city and launch query.
  Roles in none of the four (Gulf, Latin America, Africa) appear only under International.
- **Speed:** tab switches took 2–6.6 s. `companyIndex()` rebuilt the whole pool just to compare its cache key, once
  per company in the dropdown (~1.9 s); it now keys off the raw rows. `liveSkillDemand()` re-scanned every description
  on every render (~1.3 s on Global); it is now cached per region, track, floor and data. Switches now take 0.3–1.8 s.

## 2026-10-26 — PIN pad access (two PINs, 90-second idle lock)

- **Gate:** every visit opens the PIN pad. The role is never stored, and a Google session no longer grants one. There
  are two PINs, checked by salted SHA-256 (`PIN_SALT`, `PIN_HASH` in index.html). Only hashes are in the code, and
  the PINs were removed from every doc. Owner = full read, write and download. The read-only PIN (role `guest`)
  hides the Apply group, Outreach, Essays, My Profile, Settings and the dashboard profile card; dossiers lose the
  outreach templates, tailoring copilot, résumé/cover/AI generators, report download, Applied and Not-a-match.
  All downloads are blocked by a capturing `a[download]` listener (`canDownload`).
- **Wrong PINs:** denied (no guest fallback). After 5 misses the pad locks for 60 seconds.
- **Idle lock:** 90 seconds with no pointer, key, wheel, touch or scroll (or returning to the tab after that)
  brings the pad back and hides the app (`lockVault`, `body.locked`).
- setup.html checks the owner hash too. Share links (`#share=`) stay public; they show one posting's public info.
- **Limits, told to the user:** a static page plus a 4-digit PIN is a front-door lock, not real security. The hash
  can be brute-forced offline, the owner PIN was public in the repo's git history (it should be changed), and
  Supabase data is still readable with the public key until RLS is set up.

## 2026-10-26 — relocation fit

- Lisaney's rules for where to live: near water (a lake counts), a big progressive and diverse metro, not the
  South, cool or dry with snow nearby, a house with a yard for 3–4 beagles, and a strong field. They are encoded as
  `RELOC_RULES` (first match wins) with tiers in `RELOC_TIER`: Great +6, Good +2, Check closely −3, Avoid −12.
  This replaces the old Deep South −10 and the flat +5 for Seattle/LA/NZ (`DEEP_SOUTH_RE` removed). Places with
  no rule (Rochester, New Jersey, Ohio, Honolulu…) are not rated. Tiers were agreed with the user on 2026-10-26 and
  include Europe and Asia.
- **Great:** Seattle–Tacoma, LA/Long Beach/South Bay, San Diego, SF Bay Area, New Zealand, Munich, Helsinki/Espoo,
  Toronto, Berlin, Bristol.
- **Good:** Portland, Boston, Chicago, Denver–Boulder, eastern Washington, London/SE England, Barcelona, Paris,
  Luxembourg, Toulouse, Ottawa, Melbourne, Sydney, Canberra.
- **Check closely:** DC/NoVA/MD, Salt Lake City, Colorado Springs, the Antelope Valley high desert, New Mexico, East
  and South Asia.
- **Avoid:** the South (incl. the Carolinas, Tennessee, Oklahoma), Texas, Florida, Arizona, the Gulf states.
- **Where it shows:** a chip on every job row, table row and dossier, plus a line in the match breakdown, a "Where"
  filter on the Jobs page (Anywhere / Places I'd live / Great fit only), a "Places I'd live" option in the
  dashboard lists, and an "Only places I'd live" toggle on the heat maps. Dash-coded sites ("US-TX-MCKINNEY-…") are
  read as "city, state".
- `matchRules` is bumped to `fit-2026-10-26-reloc`, so cached scores rebuild.
- **Fixed (older bug):** `findJobById` returned an unscored live row, so dossiers showed no match breakdown or
  flags, and could show a different match % than the lists. It now runs `enhanceMatch` (cached).

## 2026-10-26 — job heat maps

- Every tab's dashboard has a "Where the jobs are" heat map (`heatMapPanel`, `drawHeatMap`): Global and
  International show the world, Seattle shows Washington, LA Metro shows California, US Other shows the United
  States, and New Zealand shows New Zealand (`MAP_VIEW`). Leaflet 1.9.4 and leaflet.heat 0.2.0 (jsDelivr) load only
  when a map is on screen. Tiles are OpenStreetMap standard, darkened in CSS. CARTO's dark tiles now need an API key
  and return a warning image.
- **Geocoding:** in the browser. `geo/places.json` is built from GeoNames cities5000 (CC BY 4.0) by a one-off script
  (towns of 5,000+ in the job-market countries, 50,000+ elsewhere). It's 2.2 MB, or 0.7 MB with the .htaccess
  DEFLATE. `geoOne` reads "City, State, Country", Workday "United States-California-X", RTX "US-AZ-TUCSON-805 ~ …",
  "USA - X, CA", and multi-site lists. Two-letter state codes win over country codes (IL is Illinois), and a named US
  state is binding. `GEO_EXTRA` hand-places launch sites and bases too small for the dataset. 96% of roles map;
  remote and state-only postings are left off and counted in the panel.
- State and country maps count only the sites inside their bounds. Heat is calibrated per map (98th percentile
  reaches red). The Leaflet map lives in a host element moved between renders, so tiles load once per tab, not on
  every re-render (OSM fair use).
- `deploy.yml` now publishes `geo/`.

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
