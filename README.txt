╔════════════════════════════════════════════════════════════╗
║                ORBITAL // COMMAND  —  READ ME                ║
╚════════════════════════════════════════════════════════════╝

👉  START HERE:  open  START-HERE.html  in your web browser.

That one page walks you through the whole setup in 3 simple steps
(about 15 minutes, one time). 100% browser-based — no Python to
install, no command line, no local server. If you can copy & paste,
you can do it.

------------------------------------------------------------
NEW IN THIS VERSION
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
THE 3 STEPS (full details inside START-HERE.html)
------------------------------------------------------------
1. SUPABASE  — make the free database (paste 1 block of code, press Run)
2. GITHUB    — turn on the daily job-feeder robot (add 2 secret keys)
3. IONOS     — upload the files so it's live at jobs.lisaney.com

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
