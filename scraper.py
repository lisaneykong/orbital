#!/usr/bin/env python3
"""
Orbital CRM — multi-ATS data pipeline
=====================================
Pulls REAL, active aerospace/space roles from 75 target companies across five
applicant-tracking systems (Greenhouse, Workday CXS, Lever, Ashby, Amazon) plus
custom HTML career sites, scores them against the target resume profile, maps
them to a regional hub (Seattle / Greater LA / New Zealand), reconstructs a
DIRECT-to-application URL (tracking params stripped), and upserts clean rows
into the Supabase `jobs` table.

Design rules (from the architecture master doc):
  * Never scrape a front-end career page when an ATS API exists.
  * `id`  = f"{company_slug}-{ats_id}"  (lowercase, alphanumeric + hyphens);
            custom HTML sites use  f"{name}-{md5(url)[:8]}".
  * `location_hub` is EXACTLY one of SEATTLE | GREATER_LA | NEW_ZEALAND.
  * `company` uses the exact display name (UI matches logos/colors on it).
  * `url` is the direct apply link with ?gh_jid / ?gh_src / utm_* stripped.
  * `source` is greenhouse | workday | lever | ashby | amazon | custom.
  * Writes CLEAN DATA ONLY — no synthetic / fake-row fallback.

Resilience: requests.Session() (cookie persistence), exponential backoff on
403/429 (Tenacity if installed, else a built-in fallback), a shuffled execution
queue, and structured failure logging to failed_scrapes_log.csv.

Credentials (priority order):
  1. Env vars  SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
  2. Local     config.json   (copy config.example.json -> config.json)
The SERVICE ROLE key is required for writes and must stay server-side.
"""

import os
import re
import csv
import json
import time
import random
import hashlib
import threading
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from supabase import create_client, Client

# ---- optional deps: degrade gracefully if absent -------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
    _HAS_TENACITY = True
except Exception:
    _HAS_TENACITY = False

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except Exception:
    _HAS_BS4 = False


# --------------------------------------------------------------------
# Configuration / credentials
# --------------------------------------------------------------------
def load_config():
    cfg = {}
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(here, "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
        except Exception as exc:
            print(f"!! Could not parse config.json: {exc}")

    url = os.environ.get("SUPABASE_URL") or cfg.get("supabase_url")
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
           or cfg.get("supabase_service_role_key"))
    table = os.environ.get("SUPABASE_TABLE") or cfg.get("table") or "jobs"
    threshold = int(cfg.get("alignment_threshold", 70))

    if not url or not key or "YOUR-" in str(url) or "YOUR-" in str(key):
        raise SystemExit(
            "\nMissing Supabase credentials.\n"
            "  Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as env vars,\n"
            "  or copy config.example.json -> config.json and fill it in.\n"
        )
    return url, key, table, threshold


SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE, ALIGNMENT_THRESHOLD = load_config()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept": "application/json",
})

HERE = os.path.dirname(os.path.abspath(__file__))
FAIL_LOG = os.path.join(HERE, "failed_scrapes_log.csv")
_FAIL_LOG_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()   # guards resolved_tokens.json across worker threads

# Connection pooling — reuse TCP/TLS connections across the concurrent worker pool instead
# of reconnecting per-request. Sized to comfortably cover MAX_WORKERS concurrent boards.
_adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=0)
SESSION.mount("https://", _adapter)
SESSION.mount("http://", _adapter)


# --------------------------------------------------------------------
# 75-company target dictionary (exact names + ATS tokens)
# --------------------------------------------------------------------
# Improvement #1: loaded from companies.json — the single canonical source shared
# with the browser passes (index.html/setup.html), instead of being hand-duplicated
# in three places where they could silently drift out of sync.
def _load_companies():
    path = os.path.join(HERE, "companies.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        print(f"!! Could not load companies.json ({exc}) — falling back to empty lists.")
        return {}

_COMPANIES = _load_companies()
GREENHOUSE = _COMPANIES.get("greenhouse", {})
WORKDAY = _COMPANIES.get("workday", [])
LEVER = _COMPANIES.get("lever", [])
ASHBY = _COMPANIES.get("ashby", [])
EIGHTFOLD = _COMPANIES.get("eightfold", [])
AMAZON = _COMPANIES.get("amazon", [])
WORKABLE = _COMPANIES.get("workable", [])

# Eightfold-powered portals (custom JSON API, server-side only — CORS-blocked in browser).
# API: https://{host}/api/apply/v2/jobs?domain={domain}&start=0&num=100

# Custom HTML sites. Provide a `url` (and optional CSS `selector` for posting
# links) to enable scraping; entries without a url are skipped + logged so the
# pipeline never crashes. Fill these in as you confirm each site's structure.
CUSTOM_HTML = [
    {"company": "Tethers Unlimited", "url": "https://www.tethers.com/careers/", "region": "New Zealand"},
    {"company": "Kea Aerospace", "url": "https://www.keaaerospace.com/careers", "region": "New Zealand"},
    {"company": "Astrix Astronautics", "url": "https://www.astrix.co.nz/careers", "region": "New Zealand"},
    {"company": "Argo Navis Aerospace", "url": "", "region": "New Zealand"},
    {"company": "Xerra", "url": "https://www.xerra.nz/careers/", "region": "New Zealand"},
    {"company": "SpaceBase", "url": "https://www.spacebase.co/careers", "region": "New Zealand"},
    {"company": "Tāwhaki Joint Venture", "url": "https://www.tawhaki.co.nz/careers", "region": "New Zealand"},
    {"company": "Earthpen", "url": "", "region": "New Zealand"},
    {"company": "Morf3D", "url": "", "region": "New Zealand"},
]


# --------------------------------------------------------------------
# Resume profile + scoring + gates
# --------------------------------------------------------------------
RESUME_KEYWORDS = [
    "program management", "systems engineering", "mission integration",
    "business operations", "s&op", "sales & operations planning",
    "process automation", "lifecycle management", "cross-functional",
    "stakeholder management", "salesforce", "crm", "root cause analysis",
    "regulatory compliance", "solutions engineering", "agile", "p&l",
    "scaling", "mission assurance", "payload", "launch operations",
    "supply chain", "procurement", "program operations",
]

TITLE_EXCLUDE = re.compile(
    r"\b(propulsion|gnc|guidance|navigation|thermal|structural|stress|rf engineer|"
    r"avionics|aerodynamics|flight dynamics|embedded|flight software|c\+\+|fpga|firmware|"
    r"software engineer|design engineer|mechanical engineer|electrical engineer|"
    r"technician|machinist|inspector|assembler|a&p|administrative|data scientist|ux designer)\b",
    re.I,
)
TITLE_INCLUDE = re.compile(
    r"\b(program manager|tpm|technical program|mission integration|mission manager|"
    r"operations manager|business operations|s&op|systems integration|systems engineer|systems engineering|requirements engineer|verification and validation|mbse|incose|solutions architect|"
    r"lifecycle|launch operations|supply chain|sourcing|procurement|program operations|"
    r"business development|strategy manager|operations lead|senior manager|sr\.? manager|"
    r"portfolio manager|production manager|project manager)\b",
    re.I,
)

HUB_KEYWORDS = {
    "SEATTLE": ["seattle", "redmond", "kent", "renton", "bellevue", "tukwila",
                "auburn", "everett", "bothell", "washington", " wa"],
    "GREATER_LA": ["los angeles", "hawthorne", "el segundo", "long beach",
                   "torrance", "irvine", "pasadena", "van nuys", "culver city",
                   "santa monica", "redondo beach", "manhattan beach", "inglewood",
                   "burbank", "glendale", "anaheim", "orange county", "santa clarita",
                   "palmdale"],
    "NEW_ZEALAND": ["new zealand", "mahia", "māhia", "auckland", "christchurch",
                    "wellington", " nz", "warkworth", "waikato"],
}
# Cities that are genuinely Northern California (Bay Area/Sacramento) — a bare " ca"/
# "california" match used to lump these into GREATER_LA, which was wrong.
NORCAL_KEYWORDS = ["san francisco", "bay area", "oakland", "san jose", "palo alto",
                   "mountain view", "sunnyvale", "berkeley", "redwood city",
                   "menlo park", "santa clara", "silicon valley", "sacramento"]


def determine_location_hub(loc_str):
    if not loc_str:
        return None
    low = " " + loc_str.lower()
    for hub, kws in HUB_KEYWORDS.items():
        if any(k in low for k in kws):
            return hub
    # Generic California fallback — only if NOT clearly a Bay Area / NorCal city.
    if (" ca" in low or "california" in low) and not any(k in low for k in NORCAL_KEYWORDS):
        return "GREATER_LA"
    return None


def calculate_resume_alignment(title, description):
    score = 30
    text = f"{title} {description or ''}".lower()
    score += sum(5 for kw in RESUME_KEYWORDS if kw in text)
    return min(score, 100)


def space_qualifies(title, score, is_intern, hub=None):
    t = title or ""
    if is_intern:
        return True
    if hub == "NEW_ZEALAND":
        # NZ has few space employers — keep any non-excluded role rather than
        # applying the stricter US-market alignment threshold.
        return True if not TITLE_EXCLUDE.search(t) else score >= 55
    if TITLE_EXCLUDE.search(t):
        return False
    if TITLE_INCLUDE.search(t):
        return True
    return score >= ALIGNMENT_THRESHOLD


def estimate_salary(title, hub):
    base = {"SEATTLE": 140000, "GREATER_LA": 150000, "NEW_ZEALAND": 115000}.get(hub, 140000)
    tl = (title or "").lower()
    if re.search(r"director|head|principal|lead|senior|sr\.?|manager", tl):
        sf = 1.18
    elif re.search(r"associate|junior|jr\.?|coordinator", tl):
        sf = 0.82
    else:
        sf = 1.0
    lo = round(base * sf * 0.88 / 1000) * 1000
    hi = round(base * sf * 1.16 / 1000) * 1000
    return lo, hi


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def _dedupe(seq):
    out = []
    for x in seq:
        if x and x not in out:
            out.append(x)
    return out


def gh_candidates(name, given):
    """Plausible Greenhouse board tokens for a company, best guess first."""
    base = slugify(name)
    nospace = re.sub(r"space$", "", base)
    return _dedupe([given, base, base + "space", nospace, nospace + "space",
                    base + "technologies", base + "inc", base + "corp",
                    base + "llc", base + "hq"])


def lever_candidates(name, given):
    base = slugify(name)
    nospace = re.sub(r"space$", "", base)
    return _dedupe([given, base, base + "corp", base + "inc", base + "hq", nospace])


RESOLVED_CACHE_PATH = os.path.join(HERE, "resolved_tokens.json")
def _load_resolved_cache():
    try:
        with open(RESOLVED_CACHE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}
def _save_resolved_cache(cache):
    with _CACHE_LOCK:
        try:
            with open(RESOLVED_CACHE_PATH, "w", encoding="utf-8") as fh:
                json.dump(cache, fh, indent=2)
        except Exception:
            pass
_RESOLVED_CACHE = _load_resolved_cache()


def resolve_gh(name, given):
    """Probe candidate tokens; return the one whose live board actually responds.
    Caches the winning token so subsequent runs skip re-probing every candidate."""
    cache_key = f"gh:{name}"
    cached = _RESOLVED_CACHE.get(cache_key)
    if cached:
        try:
            r = SESSION.get(f"https://boards-api.greenhouse.io/v1/boards/{cached}/jobs", timeout=12)
            if r.status_code == 200 and r.json().get("jobs"):
                return cached
        except Exception:
            pass   # cached token stopped working — fall through and re-probe
    for tok in gh_candidates(name, given):
        try:
            r = SESSION.get(
                f"https://boards-api.greenhouse.io/v1/boards/{tok}/jobs", timeout=12)
            if r.status_code == 200 and r.json().get("jobs"):
                _RESOLVED_CACHE[cache_key] = tok
                _save_resolved_cache(_RESOLVED_CACHE)
                return tok
        except Exception:
            continue
    return None


def resolve_lever(name, given):
    cache_key = f"lever:{name}"
    cached = _RESOLVED_CACHE.get(cache_key)
    if cached:
        try:
            r = SESSION.get(f"https://api.lever.co/v0/postings/{cached}?mode=json&limit=1", timeout=12)
            if r.status_code == 200 and isinstance(r.json(), list):
                return cached
        except Exception:
            pass
    for tok in lever_candidates(name, given):
        try:
            r = SESSION.get(
                f"https://api.lever.co/v0/postings/{tok}?mode=json&limit=1", timeout=12)
            if r.status_code == 200 and isinstance(r.json(), list):
                _RESOLVED_CACHE[cache_key] = tok
                _save_resolved_cache(_RESOLVED_CACHE)
                return tok
        except Exception:
            continue
    return None


def strip_tracking(url):
    """Drop ?gh_jid / ?gh_src / utm_* and other query noise from an apply URL."""
    if not url:
        return url
    try:
        parts = urllib.parse.urlsplit(url)
        q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query)
             if not (k.startswith("gh_") or k.startswith("utm_")
                     or k in ("src", "source", "ref"))]
        return urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path,
             urllib.parse.urlencode(q), ""))
    except Exception:
        return url.split("?")[0]


def clean_text(html):
    import html as _html
    text = _html.unescape(_html.unescape(html or ""))   # decode entities (twice for double-encoded)
    # Prefer a real HTML parser (BeautifulSoup) so a literal ">" inside a quoted attribute
    # value (common in Google-Docs-pasted job descriptions with data-sheets-* attributes)
    # can't leave a broken tag fragment behind, as a naive regex would.
    if _HAS_BS4:
        text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    else:
        text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------
# HTTP with retry/backoff on 403/429
# --------------------------------------------------------------------
class RetryableHTTP(Exception):
    def __init__(self, msg, retry_after=None):
        super().__init__(msg)
        self.retry_after = retry_after


def _request(method, url, **kw):
    kw.setdefault("timeout", 20)
    r = SESSION.request(method, url, **kw)
    if r.status_code in (403, 429, 502, 503):
        ra = None
        try:
            ra = float(r.headers.get("Retry-After", ""))
        except (TypeError, ValueError):
            pass
        raise RetryableHTTP(f"HTTP {r.status_code} for {url}", retry_after=ra)
    return r


if _HAS_TENACITY:
    request = retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=2, max=15),
        retry=retry_if_exception_type(RetryableHTTP),
    )(_request)
else:
    def request(method, url, **kw):
        delay = 2
        for attempt in range(4):
            try:
                return _request(method, url, **kw)
            except RetryableHTTP as exc:
                if attempt == 3:
                    raise
                wait = exc.retry_after if exc.retry_after else (delay + random.random())
                time.sleep(min(wait, 30))
                delay = min(delay * 2, 15)


def log_failure(company, url, error):
    new = not os.path.exists(FAIL_LOG)
    with _FAIL_LOG_LOCK:   # multiple worker threads may fail at once — serialize the CSV write
        try:
            with open(FAIL_LOG, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["timestamp", "company", "url", "error"])
                w.writerow([datetime.utcnow().isoformat(), company, url, str(error)[:300]])
        except Exception:
            pass


# --------------------------------------------------------------------
# Row builder (full CRM schema + enrichment)
# --------------------------------------------------------------------
def internship_signals(title, description):
    """Python mirror of the dashboard's internshipSignals() — parsed once at scrape time
    and stored as real columns so filtering/sorting can happen without re-parsing text
    client-side. Pure regex on the real scraped description; no schema dependency."""
    text = f"{title or ''} {description or ''}".lower()
    itar = bool(re.search(
        r"\bitar\b|export.control|u\.?s\.?\s*citizen(ship)?\s*(required|only|is required)?|"
        r"must be a u\.?s\.? citizen|permanent resident.{0,20}(required|status)|"
        r"export administration regulations|\bear\b\s*(compliance|regulated)", text))
    clearance = None
    if re.search(r"top secret\s*/?\s*sci|\btss?ci\b", text):
        clearance = "Top Secret/SCI"
    elif re.search(r"top secret", text):
        clearance = "Top Secret"
    elif re.search(r"secret\s+clearance|clearance.{0,15}\bsecret\b|able to obtain.{0,20}clearance", text):
        clearance = "Secret"
    elif re.search(r"security clearance", text):
        clearance = "Clearance required"
    degrees = []
    if re.search(r"\bph\.?d\.?\b|doctoral", text):
        degrees.append("PhD")
    if re.search(r"master'?s? (degree|student|candidate)|\bm\.?s\.?\b\s*(degree|program)|graduate student", text):
        degrees.append("Master's")
    if re.search(r"undergrad|bachelor'?s?|\bb\.?s\.?\b\s*(degree|program)|sophomore|junior|senior year", text):
        degrees.append("Undergrad")
    if re.search(r"freshman", text):
        degrees.append("Freshman OK")
    hw_hit = bool(re.search(
        r"hardware|cleanroom|test stand|flight hardware|hands-?on|build.{0,10}(rocket|satellite|spacecraft)|"
        r"integration (and|&) test|\bi&t\b|on-?site required", text))
    sw_hit = bool(re.search(
        r"software|firmware|embedded|algorithm|simulation|codebase|remote.friendly|hybrid", text))
    track = ("Hardware + Software" if (hw_hit and sw_hit)
             else "Hardware" if hw_hit else "Software" if sw_hit else None)
    housing = bool(re.search(
        r"housing stipend|corporate housing|relocation (assistance|stipend|package)|"
        r"temporary housing|travel stipend", text))
    skills_lex = ["C++", "Python", "MATLAB", "Simulink", "ROS", "SolidWorks", "CAD", "FPGA",
                  "Verilog", "VHDL", "LabVIEW", "ANSYS", "STK", "GNC", "CATIA", "Ada", "C#",
                  "Java", "SQL", "Linux", "Git"]
    skill_hits = [s for s in skills_lex
                  if re.search(r"(^|[^a-z0-9])" + re.escape(s.lower()) + r"([^a-z0-9]|$)", text)]
    # Real application deadline — parse an actual date out of the description instead of
    # only estimating from the posting date (mirrors the dashboard's client-side parser).
    deadline_iso = None
    months = r"january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    dm = (re.search(r"(?:application|apply|priority)?\s*(?:deadline|closes?|due)[^.\n]{0,20}?\b((?:" + months + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?|\d{1,2}/\d{1,2}(?:/\d{2,4})?)", text)
          or re.search(r"apply\s+by\s+((?:" + months + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?|\d{1,2}/\d{1,2}(?:/\d{2,4})?)", text))
    if dm:
        raw = dm.group(1)
        for fmt_year in ([raw] if ("/" in raw or re.search(r"\d{4}", raw)) else [raw + f", {datetime.utcnow().year}"]):
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m/%d/%y", "%m/%d"):
                try:
                    dt = datetime.strptime(re.sub(r"(st|nd|rd|th)", "", fmt_year), fmt)
                    if fmt == "%m/%d":
                        dt = dt.replace(year=datetime.utcnow().year)
                    if dt.year >= 2024:
                        deadline_iso = dt.isoformat()
                    break
                except Exception:
                    continue
            if deadline_iso:
                break
    # Program start date — "Summer 2026", "starting June 2026", explicit dates — distinct
    # from the application deadline, so internships can be sorted by when the program runs.
    start_iso = None
    season_m = re.search(r"\b(summer|fall|autumn|spring|winter)\s+(20\d{2})\b", text)
    if season_m:
        season_start = {"summer": 6, "fall": 9, "autumn": 9, "spring": 3, "winter": 12}
        mo = season_start.get(season_m.group(1))
        yr = int(season_m.group(2))
        if mo:
            start_iso = datetime(yr, mo, 1).isoformat()
    if not start_iso:
        sm = re.search(r"(?:start(?:ing|s)?|begins?)\s+(?:date\s*)?(?:on\s+)?((?:" + months + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}|\d{1,2}/\d{1,2}/\d{2,4})", text)
        if sm:
            raw2 = re.sub(r"(st|nd|rd|th)", "", sm.group(1))
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    start_iso = datetime.strptime(raw2, fmt).isoformat()
                    break
                except Exception:
                    continue
    return {
        "itar_flag": itar,
        "clearance_level": clearance,
        "degree_levels": ",".join(degrees) if degrees else None,
        "hw_sw_track": track,
        "housing_stipend": housing,
        "intern_skills": ",".join(skill_hits) if skill_hits else None,
        "apply_deadline": deadline_iso,
        "program_start": start_iso,
    }


def extract_intern_pay(title, description, is_intern):
    """Parse the REAL published pay/duration from the posting text — hourly rate and
    program length — instead of only ever falling back to an estimate. Returns
    (rate_per_hour_or_None, weeks_or_None)."""
    if not is_intern:
        return None, None
    text = f"{title or ''} {description or ''}"
    rate = None
    # "$28/hr", "$28.50 per hour", "$28 - $35/hour", "hourly rate of $28"
    m = re.search(r"\$\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:-|to|–)\s*\$?\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:/|per\s+)hour", text, re.I)
    if m:
        rate = round((float(m.group(1)) + float(m.group(2))) / 2)
    if rate is None:
        m = re.search(r"\$\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:/|per\s+)\s*hour", text, re.I)
        if m:
            rate = round(float(m.group(1)))
    if rate is None:
        m = re.search(r"hourly (?:rate|pay|wage)(?:\s+of)?\s*(?:is|:)?\s*\$\s*(\d{2,3}(?:\.\d{1,2})?)", text, re.I)
        if m:
            rate = round(float(m.group(1)))
    weeks = None
    m = re.search(r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s*week", text, re.I)
    if m:
        weeks = round((int(m.group(1)) + int(m.group(2))) / 2)
    if weeks is None:
        m = re.search(r"(\d{1,2})\s*week", text, re.I)
        if m:
            weeks = int(m.group(1))
    if weeks is None and re.search(r"\b10-?12\s*weeks?\b", text, re.I):
        weeks = 11
    return rate, weeks


def build_row(company, ats_id, title, location, url, source, description="", posted=None):
    title = (title or "").strip()
    if not title or not url:
        return None
    hub = determine_location_hub(location)
    if not hub:
        return None
    score = calculate_resume_alignment(title, description)
    is_intern = bool(re.search(r"\b(intern|interns?hip|co-?op|fellow(?:ship)?|summer analyst|student\s+(?:program|worker|employee)|trainee|apprentice|practicum)\b", title, re.I))
    if not space_qualifies(title, score, is_intern, hub):
        return None
    intern_rate, intern_weeks = extract_intern_pay(title, description, is_intern)

    # Use the ATS's REAL posted/updated date when it provides one — this drives the
    # scatterplot's "days on market" and the archive cutoff. Falls back to now() only
    # when the source genuinely has no date field (e.g. some custom HTML sites).
    posted_iso = None
    posting_age = 0
    if posted:
        try:
            ts = posted
            if isinstance(ts, (int, float)):
                ts = ts / 1000 if ts > 10**12 else ts
                dt = datetime.utcfromtimestamp(ts)
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
            posted_iso = dt.isoformat()
            posting_age = max(0, (datetime.utcnow() - dt).days)
        except Exception:
            posted_iso = None
    if not posted_iso:
        posted_iso = datetime.utcnow().isoformat()

    sal_min, sal_max = estimate_salary(title, hub)
    tech_terms = ["Python", "MATLAB", "Simulink", "AWS", "Azure", "Kubernetes",
                  "SQL", "Salesforce", "Tableau", "Jira", "Confluence", "Terraform"]
    body_l = (title + " " + (description or "")).lower()
    cid = f"{slugify(company)}-{ats_id}".lower()
    sig = internship_signals(title, description)

    row = {
        "id": cid,
        "company": company,
        "title": title,
        "location_hub": hub,
        "location": location or hub.replace("_", " ").title(),
        "salary_range": f"${sal_min:,} - ${sal_max:,} (est.)",
        "salary_min": sal_min,
        "salary_max": sal_max,
        "is_intern": is_intern,
        "intern_rate": intern_rate,
        "intern_weeks": intern_weeks,
        "type": "Internship" if is_intern else "Full-time",
        "match": score,
        "planets": max(0, min(5, round(score / 20))),
        "demand": score,
        "posting_age": posting_age,
        "tech": ",".join(t for t in tech_terms if t.lower() in body_l),
        "clearance": "NONE",
        "relocation_flag": False,
        "relocation_note": "-",
        "source": source,
        "status": "active",
        "saved": False,
        "archived": False,
        "url": strip_tracking(url),
        "description": clean_text(description)[:4000],
        "requirements": "",
        "timestamp": posted_iso,
        "itar_flag": sig["itar_flag"],
        "clearance_level": sig["clearance_level"],
        "degree_levels": sig["degree_levels"],
        "hw_sw_track": sig["hw_sw_track"],
        "housing_stipend": sig["housing_stipend"],
        "intern_skills": sig["intern_skills"],
        "apply_deadline": sig["apply_deadline"],
        "program_start": sig["program_start"],
    }
    return row


# --------------------------------------------------------------------
# Per-ATS extractors  -> list[row]
# --------------------------------------------------------------------
def scrape_greenhouse(token, company):
    rows = []
    real = resolve_gh(company, token)
    if not real:
        raise RetryableHTTP(f"greenhouse: no live board for {company} (tried {token} + variants)")
    r = request("GET",
                f"https://boards-api.greenhouse.io/v1/boards/{real}/jobs?content=true")
    if r.status_code != 200:
        raise RetryableHTTP(f"greenhouse {real} -> {r.status_code}")
    for j in r.json().get("jobs", []):
        jid = j.get("id")
        loc = (j.get("location") or {}).get("name", "")
        url = j.get("absolute_url") or f"https://boards.greenhouse.io/{real}/jobs/{jid}"
        row = build_row(company, jid, j.get("title"), loc, url, "greenhouse",
                        j.get("content", ""), posted=j.get("updated_at") or j.get("first_published"))
        if row:
            rows.append(row)
    return rows


def scrape_lever(token, company):
    rows = []
    real = resolve_lever(company, token)
    if not real:
        raise RetryableHTTP(f"lever: no live board for {company} (tried {token} + variants)")
    r = request("GET", f"https://api.lever.co/v0/postings/{real}?mode=json")
    if r.status_code != 200:
        raise RetryableHTTP(f"lever {real} -> {r.status_code}")
    for j in r.json():
        jid = j.get("id")
        loc = (j.get("categories") or {}).get("location", "")
        url = j.get("hostedUrl") or j.get("applyUrl")
        row = build_row(company, jid, j.get("text"), loc, url, "lever",
                        j.get("descriptionPlain") or j.get("description", ""), posted=j.get("createdAt"))
        if row:
            rows.append(row)
    return rows


def scrape_workday(cfg):
    company, tenant = cfg["company"], cfg["tenant"]
    server, board = cfg["server"], cfg["board"]
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # Workday's data-center subdomain (wd1/wd5/...) is the most error-prone token —
    # probe candidates and use whichever tenant/server actually responds.
    base = None
    for srv in _dedupe([server, "wd1", "wd5", "wd3", "wd103", "wd12", "wd2"]):
        cand = f"https://{tenant}.{srv}.myworkdayjobs.com"
        try:
            rr = SESSION.post(f"{cand}/wday/cxs/{tenant}/{board}/jobs", headers=headers,
                              data=json.dumps({"limit": 1, "offset": 0, "appliedFacets": {}}),
                              timeout=12)
            if rr.status_code == 200 and "jobPostings" in rr.text:
                base = cand
                break
        except Exception:
            continue
    if not base:
        raise RetryableHTTP(f"workday: no live tenant/server for {company} ({tenant})")
    cxs = f"{base}/wday/cxs/{tenant}/{board}/jobs"
    rows, offset, total = [], 0, None
    while True:
        # No searchText filter: we're already querying THIS company's own tenant, so an
        # extra keyword filter only risks silently excluding postings (internships in
        # particular are often titled generically — "Summer Intern", "Co-op Program" —
        # with no literal "space" in the title) that would otherwise qualify downstream.
        payload = {"limit": 20, "offset": offset, "appliedFacets": {}}
        r = request("POST", cxs, headers=headers, data=json.dumps(payload))
        if r.status_code != 200:
            raise RetryableHTTP(f"workday {tenant} -> {r.status_code}")
        data = r.json()
        if total is None:
            total = data.get("total", 0)
        postings = data.get("jobPostings", [])
        if not postings:
            break
        for p in postings:
            ext = p.get("externalPath", "") or ""
            m = re.search(r"_(R[-\d]+)\b", ext) or re.search(r"_(\w+\d+)$", ext)
            jid = m.group(1) if m else hashlib.md5(ext.encode()).hexdigest()[:8]
            url = f"{base}/en-US/{board}{ext}"
            loc = p.get("locationsText", "")
            row = build_row(company, jid, p.get("title"), loc, url, "workday",
                            p.get("title", ""), posted=p.get("postedOn") or p.get("startDate"))
            if row:
                rows.append(row)
        offset += 20
        if offset >= (total or 0) or offset >= 400:
            break
        time.sleep(0.5 + random.random())
    return rows


ASHBY_QUERY = (
    "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {"
    " jobBoard: jobBoardWithTeams(organizationHostedJobsPageName:"
    " $organizationHostedJobsPageName) { jobPostings { id title locationName"
    " employmentType } } }"
)


def scrape_ashby(cfg):
    company, token = cfg["company"], cfg["token"]
    rows = []
    url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    body = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {"organizationHostedJobsPageName": token},
        "query": ASHBY_QUERY,
    }
    r = request("POST", url, headers={"Content-Type": "application/json"},
                data=json.dumps(body))
    if r.status_code != 200:
        raise RetryableHTTP(f"ashby {token} -> {r.status_code}")
    board = (r.json().get("data") or {}).get("jobBoard") or {}
    for p in board.get("jobPostings", []):
        jid = p.get("id")
        apply_url = f"https://jobs.ashbyhq.com/{token}/{jid}"
        loc = p.get("locationName", "")
        row = build_row(company, jid, p.get("title"), loc, apply_url, "ashby",
                        p.get("title", ""), posted=p.get("publishedAt") or p.get("createdAt"))
        if row:
            rows.append(row)
    return rows


def scrape_amazon(cfg):
    company, query = cfg["company"], cfg["query"]
    rows, offset = [], 0
    while True:
        url = (f"https://www.amazon.jobs/en/search.json?base_query={query}"
               f"&offset={offset}&result_limit=100")
        r = request("GET", url)
        if r.status_code != 200:
            raise RetryableHTTP(f"amazon -> {r.status_code}")
        data = r.json()
        jobs = data.get("jobs", [])
        if not jobs:
            break
        for j in jobs:
            jid = j.get("id_icims") or j.get("id")
            loc = j.get("normalized_location") or j.get("location", "")
            apply_url = "https://www.amazon.jobs" + (j.get("job_path") or "")
            row = build_row(company, jid, j.get("title"), loc, apply_url, "amazon",
                            j.get("description_short", ""), posted=j.get("posted_date"))
            if row:
                rows.append(row)
        offset += 100
        if offset >= int(data.get("hits", 0)) or offset >= 500:
            break
        time.sleep(0.4 + random.random())
    return rows


def scrape_custom(cfg):
    company, url = cfg["company"], cfg.get("url", "")
    region_hint = cfg.get("region", "New Zealand")   # explicit per-entry, not hardcoded
    if not url:
        log_failure(company, "", "no custom URL configured")
        return []
    if not _HAS_BS4:
        log_failure(company, url, "beautifulsoup4 not installed")
        return []
    r = request("GET", url, headers={"Accept": "text/html"})
    if r.status_code != 200:
        raise RetryableHTTP(f"custom {company} -> {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    seen = set()
    sel = cfg.get("selector", "a")
    for a in soup.select(sel):
        href = a.get("href") or ""
        title = a.get_text(strip=True)
        if not href or not title or len(title) < 4:
            continue
        if not re.search(r"job|career|position|opening|role|apply", href, re.I):
            continue
        full = urllib.parse.urljoin(url, href)
        if full in seen:
            continue
        seen.add(full)
        jid = hashlib.md5(full.encode()).hexdigest()[:8]
        row = build_row(company, jid, title, company + " " + region_hint, full,
                        "custom", title)
        if row:
            rows.append(row)
    return rows


def scrape_workable(cfg):
    """Workable public widget API: returns a JSON list of postings per account token."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    api = f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=true"
    r = request("GET", api)
    if r.status_code != 200:
        raise RetryableHTTP(f"workable {token} -> {r.status_code}")
    data = r.json()
    for j in data.get("jobs", []):
        jid = j.get("shortcode") or j.get("id")
        loc_parts = [j.get("city"), j.get("state"), j.get("country")]
        loc = ", ".join([p for p in loc_parts if p])
        url = (j.get("application_url") or j.get("url")
               or f"https://apply.workable.com/{token}/j/{jid}/")
        row = build_row(company, jid, j.get("title"), loc, url, "custom",
                        j.get("description", ""), posted=j.get("published_on") or j.get("created_at"))
        if row:
            rows.append(row)
    return rows


def scrape_eightfold(cfg):
    """Eightfold career-portal JSON API (used by Virgin Galactic et al.)."""
    company, host, domain = cfg["company"], cfg["host"], cfg["domain"]
    rows, start = [], 0
    while True:
        api = (f"https://{host}/api/apply/v2/jobs?domain={domain}"
               f"&start={start}&num=100&sort_by=relevance")
        r = request("GET", api)
        if r.status_code != 200:
            raise RetryableHTTP(f"eightfold {host} -> {r.status_code}")
        data = r.json()
        positions = data.get("positions") or data.get("jobs") or []
        if not positions:
            break
        for p in positions:
            jid = p.get("id") or p.get("ats_job_id") or hashlib.md5(
                (p.get("canonicalPositionUrl") or p.get("title", "")).encode()).hexdigest()[:8]
            loc = p.get("location") or ", ".join(p.get("locations", []) or [])
            url = (p.get("canonicalPositionUrl") or p.get("apply_url")
                   or f"https://{host}/careers?pid={jid}&domain={domain}")
            row = build_row(company, jid, p.get("name") or p.get("title"), loc, url,
                            "custom", p.get("job_description") or p.get("description", ""),
                            posted=p.get("start_date") or p.get("createdOn"))
            if row:
                rows.append(row)
        total = int(data.get("count", 0) or 0)
        start += 100
        if start >= total or start >= 500:
            break
        time.sleep(0.4 + random.random())
    return rows


# --------------------------------------------------------------------
# Main scrub cycle
# --------------------------------------------------------------------
def build_tasks():
    tasks = []
    for token, name in GREENHOUSE.items():
        tasks.append((name, "greenhouse", lambda t=token, n=name: scrape_greenhouse(t, n)))
    for cfg in LEVER:
        tasks.append((cfg["company"], "lever", lambda c=cfg: scrape_lever(c["token"], c["company"])))
    for cfg in WORKDAY:
        tasks.append((cfg["company"], "workday", lambda c=cfg: scrape_workday(c)))
    for cfg in ASHBY:
        tasks.append((cfg["company"], "ashby", lambda c=cfg: scrape_ashby(c)))
    for cfg in WORKABLE:
        tasks.append((cfg["company"], "workable", lambda c=cfg: scrape_workable(c)))
    for cfg in EIGHTFOLD:
        tasks.append((cfg["company"], "eightfold", lambda c=cfg: scrape_eightfold(c)))
    for cfg in AMAZON:
        tasks.append((cfg["company"], "amazon", lambda c=cfg: scrape_amazon(c)))
    for cfg in CUSTOM_HTML:
        tasks.append((cfg["company"], "custom", lambda c=cfg: scrape_custom(c)))
    random.shuffle(tasks)   # spread load across domains naturally
    return tasks


def execute_scrub():
    print(f"\n>>> Orbital multi-ATS scrub  ({datetime.now():%Y-%m-%d %H:%M})")
    tasks = build_tasks()
    payload, total, ok_boards = [], 0, 0
    # Improvement: run boards concurrently (I/O-bound HTTP calls) instead of one at a time.
    # Bounded pool keeps us polite to any single host while cutting total wall-clock time
    # roughly in proportion to MAX_WORKERS across ~90+ boards.
    MAX_WORKERS = 8
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fn): (company, source) for company, source, fn in tasks}
        for fut in as_completed(futures):
            company, source = futures[fut]
            try:
                rows = fut.result()
                if rows:
                    ok_boards += 1
                    payload.extend(rows)
                    total += len(rows)
                    print(f"   ++ {company} [{source}]: {len(rows)} role(s)")
                else:
                    print(f"   -- {company} [{source}]: 0 matching")
            except Exception as exc:
                print(f"   !! {company} [{source}]: {exc}")
                log_failure(company, source, exc)

    # de-duplicate by id (same role can surface twice, e.g. BO greenhouse+workday)
    dedup = {row["id"]: row for row in payload}
    payload = list(dedup.values())

    # Smart cross-source de-dup: the SAME role posted to two different ATSes gets two
    # different ids, so the id-based pass above misses it. Merge anything that shares a
    # normalized (company, title, location_hub) fingerprint, keeping the richer/newer row.
    def _fingerprint(r):
        norm_title = re.sub(r"[^a-z0-9]+", " ", (r.get("title") or "").lower()).strip()
        norm_title = re.sub(r"\b(20\d{2}|summer|fall|spring|winter|intern(ship)?|co-?op)\b", "", norm_title).strip()
        return (r.get("company", "").lower(), norm_title, r.get("location_hub", ""))

    by_fp = {}
    for row in payload:
        fp = _fingerprint(row)
        prev = by_fp.get(fp)
        if prev is None:
            by_fp[fp] = row
        else:
            # keep whichever has a longer description (more complete) / more recent timestamp
            keep_new = len(row.get("description") or "") > len(prev.get("description") or "")
            by_fp[fp] = row if keep_new else prev
    merged_count = len(payload) - len(by_fp)
    payload = list(by_fp.values())
    if merged_count:
        print(f"   .. merged {merged_count} cross-source duplicate posting(s)")

    if payload:
        for i in range(0, len(payload), 100):
            chunk = payload[i:i + 100]
            _upsert_with_autoheal(chunk)
    print(f"\n>>> Complete. {len(payload)} clean row(s) from {ok_boards} board(s) "
          f"upserted into '{TABLE}'. Failures (if any) -> failed_scrapes_log.csv\n")


_SKIP_COLS = set()   # columns the live table is missing; learned once, applied to all rows


def _upsert_with_autoheal(chunk):
    """Mirror of the dashboard's fpUpsert: if the live table is missing a column
    (e.g. an older schema that predates itar_flag/clearance_level/etc.), drop that
    column and retry instead of failing the whole batch."""
    rows = [{k: v for k, v in row.items() if k not in _SKIP_COLS} for row in chunk]
    for _ in range(12):
        try:
            supabase.table(TABLE).upsert(rows).execute()
            return
        except Exception as exc:
            msg = str(exc)
            m = re.search(r"could not find the '([^']+)' column|column \"?([a-z0-9_]+)\"? of", msg, re.I)
            col = (m.group(1) or m.group(2)) if m else None
            if col and any(col in r for r in rows):
                _SKIP_COLS.add(col)
                rows = [{k: v for k, v in row.items() if k != col} for row in rows]
                continue
            print(f"   !! upsert batch failed: {exc}")
            log_failure("SUPABASE_UPSERT", TABLE, exc)
            return
    print("   !! upsert batch failed: too many schema mismatches")
    log_failure("SUPABASE_UPSERT", TABLE, "too many schema mismatches")


if __name__ == "__main__":
    execute_scrub()
