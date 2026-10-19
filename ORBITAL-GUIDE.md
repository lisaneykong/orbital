# ORBITAL — What It Is, and Why It Exists

## The Big Why

You are trying to break into the space industry — Program Management, Mission
Integration, Business Operations — and land it **fast**, because this isn't a
hobby search, it's a life change. General job boards bury space roles under
thousands of irrelevant postings, list stale/dead links, and tell you nothing
about *fit*. Orbital exists to remove every point of friction between "a space
job exists" and "you applied to it, prepared, and ready." It is built for
exactly one user — you — and nothing in it is generic.

---

## The System, Piece by Piece

### 1. The Scraper Engine (`scraper.py` + browser fetch)
Pulls **real, live** openings directly from the actual application systems
(ATS) that space companies use — Greenhouse, Lever, Ashby, Workday, Amazon,
Eightfold, Workable — across ~50+ verified real companies (SpaceX, Rocket Lab,
Blue Origin, Firefly, Starcloud, Kepler Communications, and more). It never
shows a fake or sample listing once connected — every row is a real posting
with a real, working "Apply" link. It runs automatically every day via GitHub
Actions, and you can also trigger an instant manual fetch from the app.

**Why:** so you're never wasting time on dead postings, and never missing a
new one — the pipeline never sleeps.

### 2. The Match Engine
Every role gets scored against **your real résumé** — the skills, experience,
and keywords extracted from the PDF you upload. It also weighs seniority fit,
real dealbreakers found in the text (unmet clearance, unrelated licenses), and
relocation/visa signals. An optional AI re-score can go deeper, reading the
full posting against your full résumé for a smarter semantic match.

**Why:** so you spend your limited energy on the roles you're actually
qualified for and likely to get traction on — not spraying applications.

### 3. Regional Views — Seattle · LA · New Zealand · Global
You told the system where you're willing to go. Each region has its own
dashboard, its own hiring-company chart, salary scatterplot, and — new this
build — its own real city guide, events calendar, and local news link so you
can picture actually living there.

**Why:** relocation is a real decision, not just a filter — the system treats
it that way.

### 4. Internship Intelligence
Every internship is parsed for the things that actually matter to you: ITAR /
citizenship requirements, security clearance level, degree eligibility,
hardware-vs-software track, housing stipend, real (not estimated, when
published) hourly pay, and program start/end dates. Each one also gets a
"What This Does for Your Career" note — how it ladders toward Space Ops /
Mission Integration.

**Why:** internships and early-career roles are often the fastest door in —
this makes sure you never miss the details that decide whether it's worth
your time.

### 5. My Applications (the "V-Model")
A Systems-Engineering-styled pipeline: Requirement Analysis (saved) → Concept
Design (applied) → Verification (interviewing) → Mission Validation (offer).
Every "I Applied" click is tracked with a real timestamp — no fabricated demo
data.

**Why:** a job search *is* a systems-engineering problem — this frames it that
way and keeps you honest about where every role actually stands.

### 6. Résumé + Profile
Upload your résumé from **Settings or My Profile** — both stay in sync. Every
upload re-extracts your skills automatically, so the match engine always
reflects your *current* self, not a snapshot from months ago. Your LinkedIn
URL lives right alongside it.

**Why:** your skills will grow through this search — the system is built to
grow with you, not go stale.

### 7. Live Intel Widgets
Real upcoming launch countdown (Launch Library 2), real space-industry news
(Spaceflight News API), live company hiring bars, live salary/day-on-market
scatterplots — every number on the dashboard is derived from your actual
live data, not placeholder content.

**Why:** a command console should tell the truth. Nothing on this screen
should be decoration.

### 8. The Vault (PIN 1725)
A single owner login gates editing; anyone else who opens the link gets a
read-only guest view. Simple, and yours alone.

---

## The One-Sentence Mission

**Orbital exists so that every minute you spend searching goes toward a real,
qualified, well-understood opportunity — because you are not job-hunting for
fun, you are trying to change your life, and the system should work exactly
that hard for you.**
