╔════════════════════════════════════════════════════════════╗
║                ORBITAL // COMMAND  —  READ ME                ║
╚════════════════════════════════════════════════════════════╝

👉  START HERE:  open  CLEAN-INSTALL.html  in your web browser.

That one page walks you through the whole setup in 3 simple steps
(about 15 minutes, one time). 100% browser-based — no Python to
install, no command line, no local server. If you can copy & paste,
you can do it.

------------------------------------------------------------
BUILD 17  —  CLEAN-INSTALL KIT   (build 2026-09-28.1)
------------------------------------------------------------
2026-09-28 update: index.html changed. The résumé generator and
cover letter now follow the job kit, essay answers are labelled as
drafts, and the app is live-data only: no sample jobs, and no
hardcoded chart numbers. See HANDOFF.md.

Originally this package was build 16 with nothing removed and no
app code changed. What is new is the install path: it is written to be
laid down over a database and a repo that have been reset,
rather than patched on top of a half-configured one.

· OPEN CLEAN-INSTALL.html FIRST. Six steps, in order, with the
  exact buttons to click. It replaces the ad-hoc "run this bit
  of SQL, then check that table" advice.

· SUPABASE-TELEMETRY-ONLY.sql IS NEW. scrape_runs and
  scrape_progress return 404 PGRST205 today, which is why no
  scrape has ever reported which job boards failed. On a CLEAN
  install you do not need this file — the full schema creates
  both tables. It is here for the other case: adding telemetry
  to a live database WITHOUT wiping the jobs you already have.
  The full SUPABASE-SCHEMA.sql starts with "drop table jobs".

· MANIFEST.txt IS NEW. Every file this kit should contain, so
  after uploading you can confirm nothing was missed —
  especially the hidden .github, .htaccess and .gitignore,
  which most upload tools skip unless told otherwise.

· WHAT THIS BUILD DOES NOT FIX. 39 Workday boards produce zero
  rows and 21 of them carry guessed tokens (unverified: true in
  companies.json). A clean install does not repair those. It
  makes the diagnosis possible by giving the scraper somewhere
  to record per-board outcomes; the fix comes after the first
  diagnose run, from real log output.

Carried over from build 2026-09-21.1:
· MATCHING RETUNED TO THE NEW MASTER RESUME. The engine scored
  against 34 skills; the resume claims 24. The ten extras
  included Mission Assurance, Space Mission Operations and
  Payload Integration — three the dossier simultaneously
  labelled "no experience", so a posting full of them was
  awarded full credit and then disclaimed on screen. The skill
  list is now the resume's SKILLS block verbatim, and nothing
  else. Coursework vocabulary is not lost: it scores through
  the ERAU coursework signal, which reports it honestly.

· SKILLS ARE WEIGHTED BY EVIDENCE, NOT JUST IMPORTANCE. Paid
  work counts at full weight, graduate coursework at 60%,
  transferable-but-unclaimed at 45%. The dossier's score
  breakdown now says how many of each a posting hit, so a
  number in the 80s is traceable to paid work rather than to
  keyword luck.

· POSTINGS DON'T USE RESUME WORDING. A job ad says "integrated
  master schedule", never "Schedule Management"; it says
  "cross-functional", never "Cross-functional Leadership". The
  old literal match therefore scored zero for three of the
  strongest claims on the resume on nearly every posting that
  actually wanted them. Each skill now carries the phrasings
  real postings use.

· PROGRAM MANAGEMENT IS ITS OWN ROLE TYPE. Every Program
  Manager and TPM posting — the resume's single most-targeted
  role — was being graded against Mission Integration and
  Modeling & Simulation, both seeded as no-experience. There is
  now a program archetype with the competencies those postings
  actually screen for, and it is matched first.

· THE THREE TARGETS THE RESUME NAMES NOW COUNT. Program
  Management, Technical Program Management and Systems
  Engineering get an explicit bonus. Without it, generic
  business-operations roles outranked systems-engineering ones
  — ranking the career being left above the one being entered.

· THE CLOUD SCRAPER SCORES THE SAME WAY. scraper.py's keyword
  list was one flat tier with the space-coursework terms sitting
  at top weight beside the paid-work ones. It is now three
  tiers — core 7, coursework-domain 5, supporting tooling 3 —
  so ingest-time scores and on-screen scores agree.

· PROFILE UPDATED FROM THE NEW MASTER. Summary, targeting line,
  the 8,900 kg capstone target, both sole-authored applied
  projects (the 20-year Earth-observation investment analysis
  and the air-launch / 72-satellite LEO constellation concept),
  the MCAS team project, and Siemens NX training in progress.
  The applied projects also feed essay and cover-letter
  drafting, labelled as academic work.

· MASTER RESUME SYNCED. The in-app master — the source the
  tailored resume and cover letter are generated from — carried
  employer titles and metrics that are not on your master
  document (Solutions Architect, Lifecycle Manager, 166%, 300%,
  75%). It is now the master verbatim: SoftwareOne Mid-Market
  Digital Account Manager, Achievers Account Executive, Vault.co
  Senior Manager, ServiceSource Associate Technical Specialist,
  Cornelius Ballroom President & Owner, with each role's own
  bullets. Education is split per degree with the coursework
  lines, both applied projects and the MCAS team project;
  certifications carry Siemens NX training in progress.

· NEW DIAGNOSTIC: pipeline-probe.html. Answers one question —
  has the daily Action ever written to Supabase, and if not,
  how far did it get. Reads scrape_runs and scrape_progress
  live, tells a missing table apart from an empty one, and
  names the job-board families that produced no rows at all.

Carried over from build 2026-09-11.7:
· YOUR OWN QUESTION BANK. A field in every dossier — and at
  the top of the Essay Bank page — takes a question you were
  actually asked and keeps it. Added questions appear on every
  role from then on, including roles whose real prompts you
  pasted: pasting replaces the seeded ten, never your own. Any
  answer can be marked reusable, which makes it the starting
  point on every role you have not answered yet. Questions,
  answers and reusable drafts sync across your devices with
  the rest of your tracking.

· MOBILE WAS BUILT TOO BIG. The phone breakpoint raised every
  type step by 15-21% and held every button, including dense
  inline rows inside a dossier, to a 44px minimum — so panels
  read as stacked slabs. The type step is ~7% now, radii come
  down, panel and card padding tightens, and only standalone
  controls keep the 44px floor; inline rows sit at 36-38px.
  The stat tiles were also pinned to one column by an
  !important rule that outranked the two-up grid; they are
  two-up again.

· "I APPLIED" NOW ACTUALLY RECORDS. The button lives in the
  dossier, which is injected into the page after the click
  handlers are attached — so it had no handler at all and a
  click did nothing, silently. It is on the delegated handler
  now and repaints in place the moment you tap it. Existing
  applications you thought you had marked were never saved;
  they need marking again.

· THE PIPELINE'S LAST TWO COLUMNS WERE HARDCODED EMPTY.
  Interviewing and Offer ignored the status you set in the
  cadence panel. They read it now, roles marked rejected are
  counted below the board instead of sitting in Applied, and a
  role you have applied to no longer also shows in column ①.

· DOWNLOADS REPORT THEMSELVES. The résumé, cover letter and
  match report each took several seconds in total silence —
  the first sign of life was the save dialog. All three now
  drive a progress readout with a real stage name and a
  percentage. The match report was fully synchronous, which is
  why the screen froze; it yields between stages so the bar
  can actually move.

· A FINISHED RUN NOW REPORTS ITSELF RELIABLY. The scraper's
  progress telemetry is deliberately disposable — any failure
  switches it off so a logging problem can never kill a scrape.
  But the final "this run finished" row is the one the catch-up
  gate reads to decide whether today is already done, so losing
  it to a single dropped packet meant three redundant full
  scrapes that evening. That one write now ignores the switch
  and retries. A genuinely missing table still fails fast.

· CAPSTONE COPY NO LONGER OFFERS A RECORDING. The profile, the
  résumé education bullet and three essays said the capstone
  defense was recorded and available on request. There is no
  shareable copy, so the claim is gone. The defense itself is
  still described.

· THE MATCH REPORT IS NOW THE WHOLE DOSSIER. The download on
  every role carries what the screen shows: role summary, day in
  the life, culture, score build-up, requirement-by-requirement
  coverage, coursework alignment, why-you're-suited and the
  challenge, ERAU timeline, ATS parse with the keywords to add,
  full salary breakdown against the lifestyle floor, relocation,
  all ten application essays with word counts, outreach drafts,
  alumni referral leads with live LinkedIn searches, the
  pre-submit checklist, your saved notes, and the posting text
  as an appendix.
· CUSTOM COVER LETTER on every role, downloaded as a .docx
  alongside the tailored résumé. Written from your master résumé
  only; the space background is stated as graduate coursework,
  not industry experience; anything only you can know is left as
  a [bracketed slot] and the panel counts them for you.
  "Convert Résumé" is gone — the tailored résumé replaced it.
· HONEST AI FAILURES. Rate limits and overloads retry on their
  own with backoff (up to three attempts, respecting the
  server's retry-after). An empty Anthropic credit balance is
  never retried, because retrying cannot fix it: the app says
  the key works, the account is out of credit, nothing was
  drafted, and links you to billing.
· THE IONOS PUBLISH PROVES ITSELF. It fails loudly when the
  secrets are missing, prints the folder the SFTP login actually
  lands in, and passes only when jobs.lisaney.com/build.txt
  shows the commit it just pushed. Set IONOS_REMOTE_PATH if the
  log says the upload went somewhere the web server does not
  serve. The old copy-paste workflow in START-HERE used FTPS,
  which IONOS does not speak at all — replaced.
· DEAD CODE REMOVED and the build stamp on setup.html,
  START-HERE.html and install-guide.html now matches index.html,
  so a fresh install no longer force-reloads those pages once.

Carried over from build 2026-09-09.2:
· THE WHOLE BOARD NOW LOADS. Supabase caps every reply at 1000
  rows and does it silently — a request for 2000 came back as
  exactly 1000 rows with no error at all. With 1722 roles
  scraped, 722 of them were invisible, and every count, chart
  and scatterplot was drawn on a market that was missing its
  tail. The app now pages through the table until it runs out.
  The "which configured companies produced no roles" panel was
  wrong for the same reason — it called a company missing when
  its rows simply sat past number 1000. Also fixed.
· THE SCRAPER RETRIES ITSELF. Alongside the 6:00 AM Central run
  there are now catch-up slots at roughly 10am, 2pm and 6pm.
  Each one asks the database whether today already finished; if
  it has, it stops within seconds. So a morning run killed by a
  rate limit, a quota or a network blip picks itself back up the
  same day instead of leaving the board frozen until tomorrow.
  This NEEDS the scrape_runs table — see INSTALL ORDER step 3.
  Without it the retry stays switched off and says so in the
  Actions log.
· LISTING TEMPERATURE. 🔥 Hot (1-5 days), Warm (6-10), Lukewarm
  (11-30), Cold (31-60) — on cards, dossier headers, the table
  and the snapshots. Hot means fresh AND at least a 10% match;
  recency on its own is only "new".
· MATCH FLOOR IS NOW 40%. Any higher value stored from an older
  build is pulled down once, automatically, on first load.
· 60-DAY LIVE WINDOW for full-time roles. Internships stay at
  270 days, because those programs post 6-9 months ahead of the
  start date.
· ESSAYS ON EVERY ROLE, not just internships — ten drafted
  answers per posting. Seeded questions are always labelled as a
  forecast, because real application portals cannot be read.

------------------------------------------------------------
ALSO IN THIS PACKAGE
------------------------------------------------------------
· TAILORED RÉSUMÉ — open any job, click "📄 Tailored Résumé".
  It reads the posting, tailors your summary / skills order /
  bullet order, and downloads a .docx formatted exactly like your
  master résumé. Open it in Word and export the PDF yourself.
  Your employers, titles, dates, degrees and certifications are
  never rewritten — only the three things listed above.
  Needs an Anthropic API key; it asks the first time and stores
  it in that browser only.
· MASTER RÉSUMÉ EDITOR — My Profile → "Master résumé JSON".
  This is the source the generator builds from. Edit and Save.
  It refuses to save anything that isn't valid JSON.
· M.S. SPACE SYSTEMS — the real 30-credit curriculum is now in
  the résumé data and in job matching, so roles in space cyber,
  space law/policy, Earth observation, human spaceflight,
  transportation, SATCOM and space science now score properly.
· NSLS honor society added to credentials.

------------------------------------------------------------
WHAT'S IN THIS FOLDER
------------------------------------------------------------
CLEAN-INSTALL.html .... ⭐ BUILD 17 — the six-step clean install, with
                        the exact buttons to click. Open this first.
MANIFEST.txt .......... every file this kit should contain, so you can
                        confirm an upload missed nothing
SUPABASE-TELEMETRY-ONLY.sql
                        adds scrape_runs + scrape_progress to a database
                        you do NOT want to wipe. Not needed on a clean
                        install — SUPABASE-SCHEMA.sql already makes them
START-HERE.html ....... the longer setup guide
index.html ............ your job console (the actual app)
setup.html ............ connect screen: paste keys + "Fetch real jobs"
SUPABASE-SCHEMA.sql ... the database setup SQL as a plain file
                        (same block as setup.html Step 1 — pasteable
                        straight into Supabase → SQL Editor)
companies.json ........ every company + which job board it lives on.
                        THE source of truth. scraper.py reads it, and
                        index.html's company list is generated from it.
tools.html ............ the five live diagnostic pages, explained
orbital-config.js ..... your Supabase URL + anon read key, so the site
                        works on every device without re-running setup
config.example.json ... only needed to run scraper.py on your own
                        machine. Copy to config.json and fill in.
                        GitHub Actions does NOT use it — it uses secrets.
assets/ ............... your headshot + résumé (keep this folder)
.github/ .............. the daily auto-scraper robot (GitHub runs this)
scraper.py ............ the program GitHub runs to find real space jobs
requirements.txt ...... what the scraper needs (GitHub installs it)
manifest.json ......... install the app to your phone home screen
ORBITAL-AUDIT.md ...... the full running feature list — every ask,
                        what shipped, and what's still open
.htaccess ............. static-hosting rules for IONOS
.gitignore ............ keeps runtime junk and real keys out of the repo

------------------------------------------------------------
INSTALL ORDER (full details inside START-HERE.html)
------------------------------------------------------------
0. READ CLEAN-INSTALL.html. It is the clickable version of this
   list and it is the one to follow. The steps below are the
   summary.

1. SUPABASE — Open SQL Editor → New query, paste ALL of
   SUPABASE-SCHEMA.sql, press Run. Expect "Success. No rows
   returned." On a clean install this is correct and wanted: it
   drops the jobs table, rebuilds it, and creates user_state,
   scrape_runs and scrape_progress in the same pass. Keep the
   same Supabase project — orbital-config.js already points at
   it, so a new project would mean editing that file too.

2. GITHUB — turn on the daily job-feeder. Repo → Settings →
   Secrets and variables → Actions. Add exactly two:
     SUPABASE_URL               = https://<your-ref>.supabase.co
     SUPABASE_SERVICE_ROLE_KEY  = the service_role / sb_secret_ key
   Then: Actions tab → "Orbital daily scrape" → Run workflow.

3. CONFIRM FOUR TABLES EXIST. Supabase → Table Editor. You want
   jobs, user_state, scrape_runs and scrape_progress. If
   scrape_runs is missing, the self-healing retry stays off
   silently and no run can report which boards failed. On a
   database you did NOT wipe, run SUPABASE-TELEMETRY-ONLY.sql
   instead — it adds the two tables and touches nothing else.

3b. DELETE resolved_tokens.json FROM THE REPO if GitHub shows one
   at the top level. An early package shipped it by mistake. The
   scraper trusts that cache and skips re-probing, so a stale copy
   pins companies to dead tokens and returns zero roles forever.
   It is gitignored now, but gitignore does not remove a file that
   is already committed.

4. IONOS — upload the files so the site is live at
   jobs.lisaney.com. Upload the CONTENTS of this folder, not the
   folder itself, and keep the hidden .github folder.

5. CLAUDE API KEY (only for the AI features). In the live site:
   Settings → 🔑 Claude API Key → paste → Save → Test. Wait for
   the green "✓ Working". The key is held in that one browser and
   goes nowhere else — never into these files, never to Supabase.
   Give it a monthly spend cap in the Anthropic console, since a
   key sitting in a browser is readable by anyone using that
   device.

Owner login PIN: 1725   (everyone else gets a read-only view)

To fill the console with jobs right away: open setup.html and click
"Fetch real jobs" — watch the dial climb to 100%.

------------------------------------------------------------
THE TWO GITHUB SECRETS (exact names)
------------------------------------------------------------
  SUPABASE_URL                = https://<your-ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY   = the service_role / sb_secret_ key

The workflow now checks both BEFORE it runs and tells you in plain
English what's wrong. The most common mistake by far is pasting the
anon / publishable key into the second secret — that key can only
read, so the scraper has nothing to write with. The check catches it.

To publish to IONOS automatically you also need three more:
  IONOS_FTP_SERVER · IONOS_FTP_USERNAME · IONOS_FTP_PASSWORD

Optional fourth, only if the SFTP login does not land in the folder the site is
served from (the publish workflow prints that folder and tells you):
  IONOS_REMOTE_PATH

------------------------------------------------------------
ONE THING THAT NEEDS THE INTERNET
------------------------------------------------------------
index.html loads four libraries from the internet (charts, the
database client, the PDF reader, and the Word-file writer). The
Word-file writer is pinned to docx version 9.1.0 on purpose — it
is the LAST version that publishes a browser build. 9.1.1 and
everything newer removed it, and the Tailored Résumé button will
stop working if that version number is ever raised. Leave it.

------------------------------------------------------------
IF SOMETHING FEELS STUCK
------------------------------------------------------------
· No jobs on the site?      → Actions tab → "Orbital daily scrape"
                               → Run workflow. Read the first red step.
· Want a fast health check? → Run workflow → mode: diagnose. It probes
                               one endpoint per job-board family plus
                               Supabase read AND write, in under a minute.
· "permission denied for table jobs"? → re-run SUPABASE-SCHEMA.sql.
· A company showing no roles? → open tools.html → token probe.

Scroll to the bottom of START-HERE.html for the longer list.

------------------------------------------------------------
A NOTE ON THE FILES THAT ARE *NOT* HERE
------------------------------------------------------------
resolved_tokens.json and failed_scrapes_log.csv are written by the
scraper while it runs. They are intentionally not shipped and are
gitignored (an earlier package shipped resolved_tokens.json by
mistake — it has been removed from this one): a stale resolved_tokens.json pins a company to a job-board
token that has since died, and because the scraper trusts that cache
it would stop re-probing and quietly return zero roles for that company.
