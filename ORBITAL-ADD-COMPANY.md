# Adding a company to the daily scrape

Everything you need to gather, and exactly where it goes. All field names below are verified
against `scraper.py`'s extractor functions and `index.html`'s browser pass.

---

## 1. What you need for every company, regardless of ATS

Four things. Without all four the entry either fails silently or produces rows the dashboard
throws away.

| # | Information | Why it matters |
|---|---|---|
| 1 | **Display name** — exact, human-readable ("Rocket Lab", not "rocketlab") | Written to the `company` column. The UI matches logos, colours and the company tally on this string, so it must be spelled identically everywhere it appears. |
| 2 | **Which ATS the careers page runs on** | Determines which of the eight extractors handles it, and therefore which fields you need below. |
| 3 | **The ATS identifier** (board token / tenant / query — see §3) | Usually lifted straight out of the careers-page URL. |
| 4 | **At least one posting located in a supported hub** | See §5. A company with only Denver roles used to yield nothing; it now maps to `US_OTHER`, but a company hiring solely in Munich or Toronto will still return zero rows by design. |

---

## 2. How to identify the ATS

Open the company's careers page, click a job, and read the URL you land on.

| URL you see | ATS | Bucket |
|---|---|---|
| `boards.greenhouse.io/<token>` or `job-boards.greenhouse.io/<token>` | Greenhouse | `greenhouse` |
| `jobs.lever.co/<token>` | Lever | `lever` |
| `jobs.ashbyhq.com/<token>` | Ashby | `ashby` |
| `<tenant>.wd<N>.myworkdayjobs.com/<board>` | Workday | `workday` |
| `apply.workable.com/<token>` | Workable | `workable` |
| `<token>.bamboohr.com/careers` | BambooHR | `bamboohr` |
| `<token>.jobs.personio.de` or `jobs.personio.de/<token>` | Personio | `personio` |
| `jobs.welcomekit.co/<token>` or a welcometothejungle.com board | WelcomeKit / WTTJ | `welcomekit` |
| `careers-<token>.icims.com/jobs` | iCIMS | `icims` |
| `<host>/careers` with `?domain=` on its API calls | Eightfold | `eightfold` |
| `amazon.jobs` | Amazon | `amazon` |
| Anything else (ClearCompany, Phenom, Taleo, Oracle, in-house) | — | `custom` or `careerLinks` |

If the job page is inside an iframe, right-click → "This Frame" → "Open Frame in New Tab" to see
the real ATS URL.

---

## 3. Required fields per ATS

These go in **`companies.json`**, which is the single source of truth the Python scraper reads.

### `greenhouse` — object. Two accepted value shapes
```json
"spacex": "SpaceX",
"mithril": {"company": "Mithril Technologies", "unverified": true}
```
- A plain string means the board was **confirmed against a live careers page**.
- The object form marks a **best-guess token** that has never been verified. Same behaviour at
  scrape time; the flag exists so a guess is never mistaken for a sourced value.
- **token** — the path segment after `greenhouse.io/`.
- Forgiving: `resolve_gh()` probes variants (`name`, `namespace`, `nameinc`, `namecorp`, `namehq`,
  `nametechnologies`) and caches whichever board actually responds to `resolved_tokens.json`.
  A near-miss usually self-heals.

### `lever` — array of objects
```json
{"company": "Loft Orbital", "token": "loftorbital"}
```
- **company**, **token** (path segment after `jobs.lever.co/`).
- Also variant-probed by `resolve_lever()`.

### `ashby` — array of objects
```json
{"company": "Turion Space", "token": "turion-space"}
```
- **company**, **token** (path segment after `jobs.ashbyhq.com/`; often hyphenated, sometimes with
  a suffix like `-inc`).
- **Not** variant-probed — the token must be exact.

### `workday` — array of objects. Four fields, the fiddliest of the set
```json
{"company": "Northrop Grumman", "tenant": "ngc", "server": "wd1", "board": "Northrop_Grumman_External_Site"}
```
From `https://ngc.wd1.myworkdayjobs.com/en-US/Northrop_Grumman_External_Site/job/...`:
- **tenant** — first subdomain (`ngc`). Frequently *not* the company name (Northrop = `ngc`,
  Booz Allen = `bah`, Redwire = `redwirespace`).
- **server** — the `wd1` / `wd5` / `wd3` data-centre segment. Auto-probed across
  `wd1, wd5, wd3, wd103, wd12, wd2` if you get it wrong, so a guess is acceptable.
- **board** — the site name after the locale (`Northrop_Grumman_External_Site`). **Must be exact**;
  it is not probed. Underscores and capitalisation matter.
- **company** — display name.

### `workable` — array of objects
```json
{"company": "Umbra", "token": "umbra"}
```
- **company**, **token** (path segment after `apply.workable.com/`).

### `eightfold` — array of objects
```json
{"company": "Virgin Galactic", "host": "vgcareers.virgingalactic.com", "domain": "virgingalactic.com"}
```
- **host** — the portal hostname, no scheme.
- **domain** — the value the portal passes as `?domain=` (open DevTools → Network → look at the
  `/api/apply/v2/jobs` request).
- Server-side only — CORS-blocked in the browser, so it runs in the daily Action, not a manual pass.

### `bamboohr` — array of objects
```json
{"company": "Phantom Space", "token": "phantomspace"}
```
- **token** — the subdomain before `.bamboohr.com`. Reads `/careers/list`, an unauthenticated
  JSON endpoint returning every open requisition. Widest coverage of small/mid space companies.
- Server-side only.

### `personio` — array of objects
```json
{"company": "Isar Aerospace", "token": "isaraerospace"}
```
- **token** — the subdomain in `<token>.jobs.personio.de`. The scraper reads the XML feed at
  `/xml`, not the HTML board, which is JS-rendered and unparseable.
- Server-side only.

### `welcomekit` — array of objects
```json
{"company": "Exotrail", "token": "exotrail"}
```
- **token** — the organisation reference. Two endpoint shapes exist in the wild; the extractor
  tries both and logs a miss rather than failing silently. Least reliable of the set.
- Server-side only.

### `icims` — array of objects
```json
{"company": "Example Corp", "token": "examplecorp"}
```
- **token** — the segment in `careers-<token>.icims.com`. No public JSON API, so this parses the
  search page's job links. Titles and URLs are reliable; **location often is not**, and a row with
  no parseable location is dropped at the hub gate rather than guessed at.
- Server-side only. Currently empty — populate only if you confirm a company's board parses.

### `amazon` — array of objects
```json
{"company": "Project Kuiper (Amazon)", "query": "kuiper"}
```
- **query** — the free-text search term used against `amazon.jobs`. Keep it narrow; a broad term
  pulls in unrelated Amazon roles.

### `custom` — array of objects, for career sites with no JSON API
```json
{"company": "Firefly Aerospace", "url": "https://firefly.hrmdirect.com/employment/job-openings.php?search=true", "region": "US", "selector": "a.job-title"}
```
- **company**, **url** (the page listing the jobs).
- **region** — *optional*, defaults to `"New Zealand"`. **Set this explicitly** for US companies or
  their roles land in the wrong hub.
- **selector** — *optional* CSS selector for the posting links, defaults to `"a"`. Supply one when
  the default drags in nav and footer links.
- An entry with an empty `url` is skipped and logged, never fatal.

### `careerLinks` — array of objects, not scraped at all
```json
{"company": "Lockheed Martin Space", "url": "https://www.lockheedmartinjobs.com/search-jobs/space", "note": "Phenom — no public JSON API"}
```
- **company**, **url**, **note** (why it can't be scraped).
- Use this rather than omitting a company, so the coverage gap stays visible instead of silent.

---

## 4. The second place it has to go

`companies.json` feeds the **Python scraper** (the daily GitHub Action). The **browser-side pass**
in `index.html` keeps a mirrored array, `FP_COMPANIES`, which is now **generated** from
`companies.json` — but generated at author time, not at runtime. Edit a browser-reachable bucket
and the array must be regenerated, or the in-browser refresh silently lags the daily Action.

Format is a three-element array — `[displayName, slug, type]`:

```js
['Axiom Space','axiomspace','greenhouse'],
['Spire Global','spire','lever'],
['Castelion','castelion','ashby'],
['Project Kuiper','kuiper','amazon'],
['Northrop Grumman','ngc|wd1|Northrop_Grumman_External_Site','workday'],   // pipe-joined
```

- **type** is one of `greenhouse | lever | ashby | workday | amazon`.
- For `workday`, the slug is `tenant|server|board` joined with pipes.
- `workable`, `eightfold`, `bamboohr`, `personio`, `welcomekit`, `icims` and `custom` are
  **server-side only** — do not add them to `FP_COMPANIES`; they'd be CORS-blocked in the browser.

Add to `companies.json` only → the daily Action finds it, a manual in-browser refresh doesn't.
Add to both → both passes find it.

---

## 5. What determines whether a scraped role survives

A posting is fetched successfully and then still discarded unless it clears all three gates:

1. **Location maps to a hub.** `determine_location_hub()` / `fpHubOf()` must return one of
   `SEATTLE`, `GREATER_LA`, `NEW_ZEALAND`, `US_OTHER`. Any US state name, two-letter abbreviation,
   "United States", or a US-remote posting now qualifies. Non-US, non-NZ locations return `null`
   and the row is dropped.
2. **Title passes the relevance gates.** `TITLE_EXCLUDE` kills hands-on engineering titles
   (propulsion, GNC, avionics, firmware, technician…); `TITLE_INCLUDE` admits program/ops/systems
   titles outright; anything else needs an alignment score ≥ 70. Internships bypass all of this.
3. **It has a real apply URL.** No URL, no row — there is no synthetic fallback anywhere.

So a company can be configured perfectly and still show zero roles. That's usually gate 1 or 2
doing its job, not a broken token.

---

## 6. Verifying a new entry

1. **Check the token by hand first** — paste the API URL in a browser tab:
   - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<token>/jobs`
   - Lever: `https://api.lever.co/v0/postings/<token>?mode=json`
   - Workable: `https://apply.workable.com/api/v1/widget/accounts/<token>?details=true`
   - BambooHR: `https://<token>.bamboohr.com/careers/list`
   - Personio: `https://<token>.jobs.personio.de/xml`
   - Workday: needs a POST, so easiest to confirm by loading the careers page itself.

   JSON with a populated `jobs` array means the token is right.
2. **Run the scrape** (the Action, or the in-app first pass).
3. **Read `failures.csv`** — every miss is logged there with company, URL and error. In the
   dashboard, `localStorage['orbital.scrapeHealth']` holds the last run's `failedCompanies`.
4. **Confirm rows landed** — the setup verification panel shows the per-hub counts
   (Seattle · LA · NZ · US other).

---

## 6b. Two provenance flags you will see in `companies.json`

| Flag | Meaning |
|---|---|
| `"unverified": true` | The token is a **best guess**, never confirmed against a live board. 68 entries carry it. Greenhouse and Lever tokens are variant-probed by `resolve_gh()` / `resolve_lever()`, so a near-miss often self-heals; **Ashby and Workday are not probed**, so an unverified entry there is likelier to return nothing. Confirm by hand per §6, then delete the flag. |
| `"intl": true` | The company is configured correctly but posts outside the supported hubs, so its rows are discarded after a successful fetch. See §7. |

Neither flag changes scrape behaviour. Both exist so the config distinguishes *sourced* from
*assumed*, and *broken* from *working but filtered out*.

---

## 7. The `intl` flag, and why 32 configured companies return nothing

Entries carrying `"intl": true` are fully configured and *will* be fetched, but their postings are
in Munich, Bangalore, Tokyo, Paris, Sofia, Vilnius, Copenhagen or Lisbon. `determine_location_hub()`
returns `null` for all of those, so every row is discarded after a successful fetch.

That covers Isar, PLD, Agnikul, Skyroot, Interstellar Technologies, Exotrail, ThrustMe, Enpulsion,
Pale Blue, Sateliot, Kinéis, Unseenlabs, D-Orbit, ClearSpace, Astroscale, Dhruva, Bellatrix,
EnduroSat, NanoAvionics, AAC Clyde, GomSpace, Neuraspace, Look Up, Atmos, The Exploration Company,
Airbus, Mynaric, ICEYE, Kepler and Space Forge.

They are kept in the file deliberately: several post US-based roles, which *do* survive, and the
flag documents the gap instead of hiding it. Turning the rest on requires a fifth hub
(`INTERNATIONAL`) in `REGIONS`, `fpHubOf()` and `determine_location_hub()`.

---

## 8. Minimum viable checklist for one new company

- [ ] Exact display name
- [ ] ATS identified from a real job URL
- [ ] Identifier(s) for that ATS — token, or tenant + server + board
- [ ] Confirmed the API URL returns live jobs
- [ ] Added to the right bucket in `companies.json`
- [ ] Mirrored into `FP_COMPANIES` in `index.html` (if it's a browser-reachable ATS)
- [ ] `region` set explicitly (custom entries only)
- [ ] Ran a scrape and checked `failures.csv`
