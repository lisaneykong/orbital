╔════════════════════════════════════════════════════════════╗
║                ORBITAL // COMMAND  —  READ ME                ║
╚════════════════════════════════════════════════════════════╝

👉  START HERE:  open  START-HERE.html  in your web browser.

That one page walks you through the whole setup in 3 simple steps
(about 15 minutes, one time). 100% browser-based — no Python to
install, no command line, no local server. If you can copy & paste,
you can do it.

------------------------------------------------------------
NEW IN THIS VERSION   (build 2026-09-09.6)
------------------------------------------------------------
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
START-HERE.html ....... ⭐ the simple setup guide — open this first
index.html ............ your job console (the actual app)
setup.html ............ connect screen: paste keys + "Fetch real jobs"
SUPABASE-SCHEMA.sql ... the database setup SQL as a plain file
                        (same block as setup.html Step 1 — pasteable
                        straight into Supabase → SQL Editor)
companies.json ........ every company + which job board it lives on.
                        THE source of truth. scraper.py reads it, and
                        index.html's company list is generated from it.
tools.html ............ the four live diagnostic pages, explained
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
1. SUPABASE — make the free database. Open SQL Editor → New query,
   paste ALL of SUPABASE-SCHEMA.sql, press Run. Expect
   "Success. No rows returned."

2. GITHUB — turn on the daily job-feeder. Repo → Settings →
   Secrets and variables → Actions. Add exactly two:
     SUPABASE_URL               = https://<your-ref>.supabase.co
     SUPABASE_SERVICE_ROLE_KEY  = the service_role / sb_secret_ key
   Then: Actions tab → "Orbital daily scrape" → Run workflow.

3. CHECK THE scrape_runs TABLE EXISTS. Step 1 creates it, but an
   older database that was set up before it existed will not have
   it, and the self-healing retry silently stays off. In Supabase:
   Table Editor → look for "scrape_runs" in the list. If it isn't
   there, run the scrape_runs section at the bottom of
   SUPABASE-SCHEMA.sql on its own.

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
