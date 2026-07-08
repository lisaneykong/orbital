# ORBITAL — Build Challenges &amp; Hurdles Report

*An honest retrospective on what actually went wrong along the way, why, and
how each was resolved.*

---

## 1. The "Permission Denied for Table Jobs" Saga (the biggest recurring hurdle)

This single error came back **repeatedly**, across multiple builds, for
several genuinely different underlying causes:

1. **Wrong key pasted.** Early on, the anon (read-only) key was pasted into
   the service_role field by mistake — the two keys look nearly identical.
   Fixed by adding a JWT decode step that reads the key's actual `role`
   claim and refuses to proceed with a clear message if it isn't
   `service_role`.
2. **Table never actually created / partially created.** The original SQL
   used `create table if not exists`, which silently does *nothing* if an
   older, incompatible table already existed — so re-running the "fix" SQL
   never actually fixed anything. Solved by rewriting the SQL to
   `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for every field, so re-running
   it genuinely upgrades an old table in place.
3. **Missing GRANTs / Row-Level Security.** Even with the correct key and a
   correct table, Postgres still blocked writes because the `service_role`
   had never been explicitly granted write privileges, and RLS was enabled
   with no write policy. Solved by adding explicit `GRANT` statements and
   disabling RLS for this single-user tool.
4. **Browser autofill silently swapping the two key fields.** After all of
   the above was fixed, the error came back one more time — this time
   traced to the browser/password manager overwriting the anon-key field
   with the service-role key after submit, because the two adjacent
   JWT-like fields pattern-matched as "the same login." Solved with
   autofill-hardening attributes and a hard guard that refuses to proceed
   if both fields ever end up identical.
5. **A live Supabase platform incident.** At one point, the same error
   showed up even though everything above was correctly configured — a
   pasted Supabase status-page log confirmed an active, ongoing capacity
   incident on their infrastructure. This was the one cause genuinely
   outside our control; the fix was simply "wait and retry."

**Lesson:** one error message, five distinct root causes over the course of
the build. Each fix was real and necessary — none of them were wasted work,
even though it felt like whack-a-mole in the moment.

---

## 2. Local-Install Confusion → Full Pivot to Cloud-Only

The build started with a Windows-oriented local installer (`install.bat`,
`start-build.ps1`, a Python-based local seed script). This produced real,
concrete pain: PowerShell parse errors, confusion about what needed to run
"on your computer" vs. online, and a fundamental mismatch with the actual
goal — a site hosted at `jobs.lisaney.com` that should run **100% online**.

**Resolution:** the entire local-run path was deleted. Every install step
was rebuilt around three cloud services wired together (Supabase, GitHub
Actions, IONOS), with an explicit "you never run anything on your own
computer" guarantee. This was a full architectural pivot mid-build, not a
small patch — and it was the right call once the actual requirement (always
online, zero local dependency) was clear.

---

## 3. Multiple Rounds of "It Doesn't Match What I See"

Several bugs shared the same shape: **the UI showed a number that didn't
match reality**, and each had a different cause:

- **"Top Hiring Companies" chart showed a hardcoded fake count** (e.g.
  "Rocket Lab 76") while the actual job list showed only 2 real roles. Root
  cause: the chart was reading a static sample dataset instead of the live
  loaded rows. Fixed by tallying the chart directly from the actual jobs in
  memory.
- **CA/LA region miscounting.** A generic "California" text match was
  bucketing Bay Area roles (San Francisco, Palo Alto) into the Greater LA
  region, inflating that count and misplacing roles. Fixed with an explicit
  NorCal-city exclusion list across all three engines (dashboard, setup
  page, and the Python scraper).
- **Scatterplot didn't match "days listed."** The chart was plotting a
  separate sample dataset with its own fake day-count logic instead of the
  same live rows shown in the list below it. Fixed by pointing the chart at
  the identical live data source.
- **"$0/hr" and "0w" on internships** with no real scraped pay — a classic
  default-value bug (`internRate || 0` treated as a real number instead of
  "no data"). Fixed to show a properly labeled estimate instead of a false
  zero.

**Lesson:** any time a summary/chart view and a detail/list view are backed
by *different* data sources, they will eventually disagree — the fix in
every case was making sure there was exactly one source of truth per
region/track.

---

## 4. Fabricated Content Discovered in Multiple Passes

Across several "deep scan" requests, real fabricated content kept surfacing
that had been present from earlier in the build and not yet questioned:

- A fake Zillow listing, a static Nashville-vs-target weather comparison,
  fake "applied/interview/offer" demo pipeline data, a hardcoded news
  ticker, a static "Next Launch" countdown with made-up mission details, a
  hardcoded space-news list, a fabricated Events calendar (complete with
  fake "RFP awarded" procurement claims), fabricated City Culture claims
  (invented festival names/dates, real artist names attached to made-up
  claims), and a fully dead `GLOBAL_REGIONS` dataset (fake companies like
  "OpenNova," "Datastream") feeding an unreachable function.

**Resolution:** each was individually replaced — either with a genuine live
API (Launch Library 2 for missions, Spaceflight News API for news), an
honest real-source link-out (Events, City Culture), or deleted outright
(the dead `GLOBAL_REGIONS` code). This took several dedicated passes because
each fix required actually researching a real, free, keyless API or a real
authoritative source — not just deleting the fake content.

**Lesson:** "looks impressive" and "is true" are different bars, and a build
this size accumulates the former unless specifically audited for the
latter, repeatedly.

---

## 5. A Filter-State Bug That Looked Like a Data Problem

When internship links stopped responding to clicks, the natural assumption
was "the data isn't there." The actual cause was structural: clicking a job
called a lookup function that re-applied the *current* page's active
filters (region/track) before finding the job — so an internship shown in a
filter-agnostic widget (Early-Career Radar, Featured Internship banner)
would get excluded by the currently-active "Full-time" filter during lookup,
and the click would silently do nothing.

**Resolution:** the lookup was changed to always search the full, unfiltered
dataset by ID, independent of whatever filters happen to be active
elsewhere on the page.

**Lesson:** "nothing happens when I click" is often not a missing-data bug —
it's a mismatch between what's *displayed* and what's *searched*.

---

## 6. Two Accidental Mid-Edit Breaks (Caught and Fixed)

On at least two occasions during large restructuring edits (once in the
mission-panel rewrite, once in a job-list reformat), a str_replace edit left
a duplicated function header or an orphaned closing tag, breaking the
JavaScript compile. Both were caught immediately by a compile-check step run
right after the edit, and fixed before being shown to you.

**Lesson:** large edits to a single, growing HTML file carry real risk of
this kind of break — which is why every substantive change in this build was
followed by an explicit "does this still compile" check rather than assuming
success.

---

## 7. Résumé/LinkedIn Ingestion Needed Real Engineering, Not Just a Form Field

Early on, "let me upload my résumé" seemed like a simple file input. It
actually required: PDF text extraction in the browser (pdf.js), a real
skill-detection engine against a curated aerospace/ops keyword lexicon,
wiring that extracted data into the *live* match-scoring algorithm (not just
displaying it), handling large-file storage-quota failures gracefully, and
eventually duplicating that whole pipeline into a second location (My
Profile) while keeping both in sync.

**Lesson:** "just add an upload button" asks often hide a full feature's
worth of real engineering underneath.

---

## Summary

The recurring theme across every hurdle in this build: **the first
explanation is rarely the whole explanation.** "Permission denied" was five
different bugs across the build's lifetime. "The number is wrong" was four
different disconnected-data-source bugs. "Nothing happens" was a filter
mismatch, not missing data. Each hurdle got fully resolved by refusing to
stop at the first plausible cause and verifying the actual mechanism —
which is also exactly why the system today is in a genuinely solid,
real-data state rather than a set of surface-level patches.
