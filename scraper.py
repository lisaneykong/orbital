#!/usr/bin/env python3
"""
Orbital CRM — multi-ATS data pipeline
=====================================
Pulls REAL, active aerospace/space roles from ~200 target companies across nine
applicant-tracking systems (Greenhouse, Workday CXS, Lever, Ashby, Amazon,
Workable, Eightfold, BambooHR, Personio, WelcomeKit/WTTJ, iCIMS) plus
custom HTML career sites, scores them against the target resume profile, maps
them to a regional hub (Seattle / Greater LA / New Zealand), reconstructs a
DIRECT-to-application URL (tracking params stripped), and upserts clean rows
into the Supabase `jobs` table.

Design rules (from the architecture master doc):
  * Never scrape a front-end career page when an ATS API exists.
  * `id`  = f"{company_slug}-{ats_id}"  (lowercase, alphanumeric + hyphens);
            custom HTML sites use  f"{name}-{md5(url)[:8]}".
  * `location_hub` is EXACTLY one of SEATTLE | GREATER_LA | NEW_ZEALAND | US_OTHER |
    INTERNATIONAL.
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

import os, sys
import re
import csv
import json
import time
import random
import hashlib
import threading
import urllib.parse
from datetime import datetime, timezone
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
BAMBOOHR = _COMPANIES.get("bamboohr", [])
PERSONIO = _COMPANIES.get("personio", [])
WELCOMEKIT = _COMPANIES.get("welcomekit", [])
ICIMS = _COMPANIES.get("icims", [])
# Buckets added by the 2026-09-06 route passes. Each one needs BOTH an entry here and a
# loop in build_tasks(), or the board sits in companies.json and is never fetched.
SMARTRECRUITERS = _COMPANIES.get("smartrecruiters", [])
RECRUITEE = _COMPANIES.get("recruitee", [])
BREEZY = _COMPANIES.get("breezy", [])
RIPPLING = _COMPANIES.get("rippling", [])
PINPOINT = _COMPANIES.get("pinpoint", [])
MANATAL = _COMPANIES.get("manatal", [])

# Eightfold-powered portals (custom JSON API, server-side only — CORS-blocked in browser).
# API: https://{host}/api/apply/v2/jobs?domain={domain}&start=0&num=100

# Custom HTML sites. Provide a `url` (and optional CSS `selector` for posting
# links) to enable scraping; entries without a url are skipped + logged so the
# pipeline never crashes. Fill these in as you confirm each site's structure.
# companies.json owns this list. The hardcoded fallback that used to live here shadowed
# it whenever the custom bucket was empty, so edits to the file appeared to do nothing.
CUSTOM_HTML = _COMPANIES.get("custom", [])


# --------------------------------------------------------------------
# Resume profile + scoring + gates
# --------------------------------------------------------------------
RESUME_KEYWORDS = [
    # Mirrors OWNER.skills in index.html, which is generated from the two current resume
    # versions (master + General Dynamics tailored). Keep the two in sync: this list is
    # what calculate_resume_alignment() scores against at ingest time.
    "systems engineering",
    "requirements development",
    "requirements management",
    "verification and validation",
    "trade study",
    "trade studies",
    "program management",
    "technical program",
    "technical project management",
    "project management",
    "mission integration",
    "mission operations",
    "mission assurance",
    "space operations",
    "spacecraft operations",
    "payload integration",
    "schedule management",
    "integrated master schedule",
    "critical path",
    "risk management",
    "risk mitigation",
    "lifecycle management",
    "configuration management",
    "interface control",
    "concept of operations",
    "conops",
    "design review",
    "integration and test",
    "work breakdown",
    "budget",
    "resource planning",
    "capacity planning",
    "stakeholder management",
    "cross-functional",
    "process automation",
    "root cause analysis",
    "supplier negotiation",
    "regulatory compliance",
    "operational excellence",
    "agile",
    "ms project",
    "jira",
    "python",
    "tableau",
    "power bi",
    "salesforce",
    "proposal",
    "p&l",
    "startup",
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
    # SEATTLE and GREATER_LA moved to the regexes below. "washington" used to live in the
    # SEATTLE list, which filed every "Washington, D.C." posting as a Seattle role — the
    # dict is ordered, so DC never reached the US_OTHER branch. D.C. is now excluded first.
    "NEW_ZEALAND": ["new zealand", "mahia", "māhia", "auckland", "christchurch",
                    "wellington", " nz", "warkworth", "waikato"],
}

# ---- Hub geography. Kept deliberately in step with fpHubOf() in index.html; when the two
# ---- disagree, the browser pass and the nightly Action file the same job in two hubs.
DC_RE = re.compile(r"washington,?\s*d\.?c\.?|district of columbia")
WA_STATE_RE = re.compile(r"\bwa\b|washington state|,\s*washington\b")
PNW_CITY_RE = re.compile(
    r"seattle|seatle|redmond|kent|renton|bellevue|tukwila|auburn|everett|kirkland|bothell|"
    r"lynnwood|mukilteo|woodinville|issaquah|sammamish|federal way|sea-?tac|tacoma|olympia|"
    r"puyallup|marysville|snohomish|dupont|lacey|edmonds|shoreline|burien|kenmore|"
    r"mill creek|bremerton")
LA_METRO_RE = re.compile(
    r"los angeles|hawthorne|el segundo|long beach|torrance|irvine|pasadena|van nuys|"
    r"culver city|santa monica|redondo beach|manhattan beach|inglewood|burbank|glendale|"
    r"anaheim|orange county|santa clarita|palmdale|huntington beach|mojave|lancaster|"
    r"downey|carson|gardena|compton|chatsworth|northridge|woodland hills|sylmar|valencia|"
    r"canoga park|santa ana|costa mesa|tustin|fullerton|brea|cerritos|signal hill|"
    r"seal beach|garden grove|simi valley|thousand oaks|camarillo|oxnard|ventura|goleta|"
    r"san pedro|sun valley|el monte|whittier|norwalk|la mirada|city of industry|"
    r"santa fe springs|monrovia|azusa|covina|pomona|rancho cucamonga|san bernardino|"
    r"riverside|westminster,? ca|ontario,? ca|corona,? ca")
NORCAL_RE = re.compile(
    r"san francisco|bay area|oakland|san jose|palo alto|mountain view|sunnyvale|berkeley|"
    r"redwood city|menlo park|santa clara|silicon valley|sacramento|burlingame|san mateo|"
    r"san carlos|foster city|south san francisco|fremont|hayward|emeryville|alameda|"
    r"milpitas|cupertino|los altos|campbell|san leandro|livermore|pleasanton|san ramon|"
    r"walnut creek|novato|san rafael|petaluma|santa rosa|vacaville|morgan hill|gilroy|"
    r"watsonville|santa cruz|monterey|salinas|napa|vallejo|stockton|modesto|dublin,? ca|"
    r"concord,? ca|richmond,? ca|davis,? ca|fairfield,? ca")
# "Burlingame, California" matched no city list and no state name in US_OTHER_RE, so it
# returned None and the row was thrown away. Spelled-out California now counts.
CA_STATE_RE = re.compile(r"\bca\b|,\s*california\b|\bcalifornia,")
# Bare metro names with no state or country attached, which were being discarded.
US_METRO_RE = re.compile(
    r"\baustin\b|\bboulder\b|\bdenver\b|wichita|huntsville|albuquerque|pittsburgh|"
    r"\bhouston\b|\bdallas\b|\bphoenix\b|\btucson\b|salt lake|colorado springs|"
    r"cape canaveral|titusville|\bmidland\b|\bchicago\b|\bboston\b|\batlanta\b|"
    r"\bportland\b|san diego|folsom|d\.?c\.? office")
INTL_EXTRA_RE = re.compile(r"kyiv|kiev|lviv|loughborough|new dehli|\beurope\b|middle east|\blatam\b")

# Fourth hub: the rest of the United States. Without this, roles from the primes and
# integrators (Colorado, Texas, Alabama, Virginia, Florida) scraped fine and were then
# discarded for having no hub.
# Fifth hub: commercial space outside the US and NZ. Matched BEFORE US_OTHER because
# two-letter country codes collide with state abbreviations (DE, IN, CA, IL, CO, MA);
# ambiguous city names with US namesakes (Melbourne FL, Vienna VA, Paris TX) are matched
# AFTER US_OTHER so the US reading wins.
INTL_RE = re.compile(
    r"canada|united kingdom|\bu\.?k\.?\b|england|scotland|wales|northern ireland|ireland|"
    r"france|germany|deutschland|italy|italia|spain|españa|portugal|netherlands|holland|"
    r"belgium|luxembourg|switzerland|austria|denmark|sweden|norway|finland|iceland|poland|"
    r"czech|slovakia|hungary|romania|bulgaria|greece|croatia|slovenia|turkey|türkiye|estonia|"
    r"latvia|lithuania|ukraine|israel|united arab emirates|\buae\b|saudi|qatar|oman|bahrain|"
    r"kuwait|jordan|egypt|morocco|south africa|kenya|ghana|nigeria|india|japan|south korea|"
    r"singapore|malaysia|indonesia|thailand|vietnam|philippines|taiwan|hong kong|australia|"
    r"brazil|brasil|argentina|chile|mexico|méxico|colombia|peru|uruguay|international|emea|"
    r"\bapac\b|toulouse|kourou|bordeaux|nantes|grenoble|montpellier|sophia antipolis|"
    r"bengaluru|bangalore|hyderabad|chennai|mumbai|ahmedabad|new delhi|tokyo|osaka|fukuoka|"
    r"tsukuba|hokkaido|seoul|daejeon|shenzhen|taipei|tel aviv|herzliya|haifa|beersheba|"
    r"harwell|guildford|farnborough|stevenage|didcot|oxfordshire|münchen|munich|bremen|"
    r"augsburg|stuttgart|darmstadt|köln|oberpfaffenhofen|noordwijk|delft|eindhoven|leuven|"
    r"liège|lausanne|zürich|zurich|gothenburg|göteborg|kiruna|trondheim|tromsø|espoo|tampere|"
    r"tartu|tallinn|vilnius|kaunas|wrocław|warszawa|brno|thessaloniki|ankara|istanbul|dubai|"
    r"abu dhabi|riyadh|jeddah|torino|milano|bologna|napoli|catania|barcelona|sevilla|elche|"
    r"lisboa|coimbra|brisbane|adelaide|canberra|mount stromlo|koonibba|whyalla|montréal|"
    r"longueuil|st-hubert|mississauga|brampton|winnipeg|são paulo|santiago|buenos aires|"
    r"querétaro|stellenbosch|johannesburg|pretoria|nairobi",
    re.I,
)
INTL_AMBIGUOUS_RE = re.compile(
    r"melbourne|sydney|perth|vienna|berlin|paris|milan|rome|athens|naples|bristol|oxford|"
    r"cambridge|glasgow|edinburgh|birmingham|london|toronto|ottawa|vancouver|calgary|madrid|"
    r"lisbon|prague|warsaw|sofia|bucharest|copenhagen|stockholm|oslo|helsinki|amsterdam|"
    r"brussels|luxembourg city|cape town|mexico city|delhi",
    re.I,
)

US_OTHER_RE = re.compile(
    r"united states|\bu\.?s\.?a?\b|remote,? us|remote \(us|"
    r"alabama|alaska|arizona|arkansas|colorado|connecticut|delaware|florida|georgia|"
    r"hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|"
    r"massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|"
    r"new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|"
    r"oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|"
    r"texas|utah|vermont|virginia|west virginia|wisconsin|wyoming|district of columbia|"
    r"washington,? d\.?c\.?|"
    r"\b(?:al|ak|az|ar|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|"
    r"ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wv|wi|wy|dc)\b",
    re.I,
)


def determine_location_hub(loc_str):
    """Mirror of fpHubOf() in index.html. Order matters: D.C. is settled before any
    Washington test, and NorCal is claimed before the bare-California fallback."""
    if not loc_str:
        return None
    low = " " + loc_str.lower()
    is_dc = bool(DC_RE.search(low))
    if not is_dc and (WA_STATE_RE.search(low) or PNW_CITY_RE.search(low)):
        return "SEATTLE"
    for hub, kws in HUB_KEYWORDS.items():
        if any(k in low for k in kws):
            return hub
    if LA_METRO_RE.search(low):
        return "GREATER_LA"
    if NORCAL_RE.search(low):
        return "US_OTHER"
    if CA_STATE_RE.search(low):
        return "GREATER_LA"
    if INTL_RE.search(low):
        return "INTERNATIONAL"
    if US_OTHER_RE.search(low):
        return "US_OTHER"
    if INTL_AMBIGUOUS_RE.search(low):
        return "INTERNATIONAL"
    if US_METRO_RE.search(low):
        return "US_OTHER"
    if INTL_EXTRA_RE.search(low):
        return "INTERNATIONAL"
    # Deliberately unmapped: "Remote", "Talent Community", "Flexible - Any SpaceX Site".
    # They carry no place, and inventing a hub would stamp a fabricated location on a
    # real posting. coverage-seattle-la.html lists whatever lands here.
    return None


# Tiered weighting mirrors OWNER.coreSkills in index.html: the credentials and functions
# Lisaney is actually targeting count for more than the supporting tooling. A flat +5 per
# term made the 70% firewall need 8 hits, so genuinely-matching roles stalled in the 40s.
RESUME_CORE = [
    "systems engineering", "requirements development", "requirements management",
    "verification and validation", "trade study", "trade studies",
    "technical program", "technical project management", "program management",
    "mission integration", "mission operations", "mission assurance",
    "space operations", "spacecraft operations", "payload integration",
    "schedule management", "integrated master schedule", "critical path",
    "concept of operations", "conops", "interface control",
]


def calculate_resume_alignment(title, description):
    """Tiered keyword alignment. A hit in the TITLE is worth double a hit in the body:
    a title states what the job is, a body line is only context."""
    title_l = (title or "").lower()
    body_l = f"{title or ''} {description or ''}".lower()
    score = 30
    for kw in RESUME_KEYWORDS:
        if kw not in body_l:
            continue
        weight = 7 if kw in RESUME_CORE else 3
        if kw in title_l:
            weight *= 2
        score += weight
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
    base = {"SEATTLE": 140000, "GREATER_LA": 150000, "NEW_ZEALAND": 115000,
            "US_OTHER": 135000, "INTERNATIONAL": 105000}.get(hub, 140000)
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
    with _FAIL_LOG_LOCK:   # multiple worker threads may fail at once — serialize the CSV write
        # The existence check has to happen INSIDE the lock. Computed outside it, every
        # thread that failed at once saw no file and wrote its own header row, which is
        # why the shipped log had "timestamp,company,url,error" repeated through it.
        new = not os.path.exists(FAIL_LOG)
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
VERTICAL_RE = {
    # Python mirror of the dashboard's VERTICAL_RE (index.html) — keep the two in sync.
    # Classified at ingest against the FULL description (before the 4000-char storage
    # truncation), so the stored signal can be richer than client-side re-parsing.
    "gnc": re.compile(
        r"\bgnc\b|guidance|orbital mechanics|astrodynamic|flight dynamics|matlab|simulink|"
        r"\bstk\b|trajector|orbit determination|attitude (control|determination)", re.I),
    "ground": re.compile(
        r"ground segment|ground station|ground software|ground system|\blinux\b|\bunix\b|"
        r"\bpython\b|c\+\+|\baws\b|\bazure\b|\bcloud\b|devops|constellation op", re.I),
    "mission": re.compile(
        r"telemetry|hardware.?in.?the.?loop|\bhitl\b|anomal(y|ies)|mission assurance|"
        r"validation|verification|error log|diagnostic", re.I),
}


def classify_verticals(title, description):
    """Domain-vertical classification (guide §4: GNC / Ground Segment / Mission Assurance).
    Returns a comma-joined key string, or "" when classification ran but nothing matched —
    the empty string tells the dashboard *not* to fall back to client-side re-parsing."""
    text = f"{title or ''} {description or ''}"
    return ",".join(k for k, rx in VERTICAL_RE.items() if rx.search(text))


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
        "description": clean_text(description)[:12000],
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
        "verticals": classify_verticals(title, description),
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


def _workday_description(base, tenant, board, ext):
    """Workday's job LIST endpoint carries NO description — only the per-job detail endpoint
    does. Until this existed the pipeline stored the job TITLE as the description, which
    starved every downstream consumer: resume alignment, vertical classification, ITAR and
    clearance parsing, intern pay extraction and deadline parsing all read that field.
    Called only for postings whose location already resolved to a target hub, so this costs
    one request per KEPT row rather than one per posting."""
    if not ext:
        return ""
    try:
        r = request("GET", f"{base}/wday/cxs/{tenant}/{board}{ext}",
                    headers={"Accept": "application/json"})
        if r.status_code != 200:
            return ""
        info = (r.json() or {}).get("jobPostingInfo") or {}
        return (info.get("jobDescription")
                or info.get("jobDescriptionSummary")
                or info.get("jobRequisitionDescription") or "")
    except Exception:
        return ""


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
            loc = p.get("locationsText", "")
            # Cheap local gate BEFORE paying for a detail request: most postings sit
            # outside the target hubs and build_row would drop them anyway.
            if not determine_location_hub(loc):
                continue
            m = re.search(r"_(R[-\d]+)\b", ext) or re.search(r"_(\w+\d+)$", ext)
            jid = m.group(1) if m else hashlib.md5(ext.encode()).hexdigest()[:8]
            url = f"{base}/en-US/{board}{ext}"
            desc = _workday_description(base, tenant, board, ext)
            row = build_row(company, jid, p.get("title"), loc, url, "workday",
                            desc, posted=p.get("postedOn") or p.get("startDate"))
            if row:
                rows.append(row)
            time.sleep(0.25 + random.random() * 0.25)
        offset += 20
        if offset >= (total or 0) or offset >= 400:
            break
        time.sleep(0.5 + random.random())
    return rows


ASHBY_QUERY = (
    "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {"
    " jobBoard: jobBoardWithTeams(organizationHostedJobsPageName:"
    " $organizationHostedJobsPageName) { jobPostings { id title locationName"
    " employmentType descriptionPlain } } }"
)


def scrape_ashby(cfg):
    company, token = cfg["company"], cfg["token"]
    rows = []
    # Ashby's DOCUMENTED public posting API returns descriptionPlain. The internal GraphQL
    # board query below does not reliably, and this extractor previously passed the job
    # TITLE in as the description. Verified live 2026-09-05 against impulse / iceye /
    # skylo / sift / astra / outpost / turion-space / reflect-orbital / hadrian-automation.
    try:
        r = request("GET",
                    f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true",
                    headers={"Accept": "application/json"})
        if r.status_code == 200:
            postings = (r.json() or {}).get("jobs")
            if postings is not None:
                for p in postings:
                    jid = p.get("id")
                    loc = (p.get("location")
                           or ((p.get("address") or {}).get("postalAddress") or {}).get("addressLocality")
                           or "")
                    apply_url = (p.get("jobUrl") or p.get("applyUrl")
                                 or f"https://jobs.ashbyhq.com/{token}/{jid}")
                    row = build_row(company, jid, p.get("title"), loc, apply_url, "ashby",
                                    p.get("descriptionPlain") or p.get("descriptionHtml") or "",
                                    posted=p.get("publishedAt") or p.get("updatedAt"))
                    if row:
                        rows.append(row)
                return rows
    except Exception:
        pass   # fall through to the GraphQL board query

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
                        p.get("descriptionPlain") or "",
                        posted=p.get("publishedAt") or p.get("createdAt"))
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
                            j.get("description") or j.get("description_short", ""),
                            posted=j.get("posted_date"))
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


def scrape_bamboohr(cfg):
    """BambooHR public careers JSON. /careers/list returns every open requisition for the
    account with no auth. Covers the largest single block of small/mid space companies."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    api = f"https://{token}.bamboohr.com/careers/list"
    r = request("GET", api)
    if r.status_code != 200:
        raise RetryableHTTP(f"bamboohr {token} -> {r.status_code}")
    for j in (r.json().get("result") or []):
        loc = j.get("location") or {}
        if isinstance(loc, dict):
            loc_str = ", ".join([p for p in (loc.get("city"), loc.get("state"),
                                             loc.get("country")) if p])
        else:
            loc_str = str(loc or "")
        if not loc_str and (j.get("isRemote") or j.get("atsLocationRemote")):
            loc_str = "Remote"
        jid = j.get("id") or j.get("jobOpeningId")
        row = build_row(company, jid, j.get("jobOpeningName"), loc_str,
                        f"https://{token}.bamboohr.com/careers/{jid}", "custom",
                        j.get("departmentLabel") or "")
        if row:
            rows.append(row)
    return rows


def scrape_personio(cfg):
    """Personio XML job feed — the reliable public endpoint (the HTML board is JS-rendered)."""
    import xml.etree.ElementTree as ET
    company, token = cfg["company"], cfg["token"]
    rows = []
    api = f"https://{token}.jobs.personio.de/xml"
    r = request("GET", api)
    if r.status_code != 200:
        raise RetryableHTTP(f"personio {token} -> {r.status_code}")
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as exc:
        raise RetryableHTTP(f"personio {token} bad xml: {exc}")
    for pos in root.iter("position"):
        def g(tag):
            el = pos.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        jid = g("id")
        loc = ", ".join([p for p in (g("office"), g("subcompany")) if p])
        desc = " ".join((el.text or "") for el in pos.iter("value"))
        row = build_row(company, jid, g("name"), loc,
                        f"https://{token}.jobs.personio.de/job/{jid}", "custom",
                        desc, posted=g("createdAt") or None)
        if row:
            rows.append(row)
    return rows


def scrape_welcomekit(cfg):
    """Welcome to the Jungle / WelcomeKit. Two endpoint shapes in the wild; try both and
    let the failure log record it rather than guessing silently."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    endpoints = [
        f"https://api.welcometothejungle.com/api/v1/organizations/{token}/jobs",
        f"https://www.welcomekit.co/api/v1/embed/organizations/{token}/jobs",
    ]
    data = None
    for api in endpoints:
        r = request("GET", api)
        if r.status_code == 200:
            try:
                data = r.json()
                break
            except Exception:
                continue
    if data is None:
        raise RetryableHTTP(f"welcomekit {token} -> no usable endpoint")
    jobs = data.get("jobs") or data.get("results") or (data if isinstance(data, list) else [])
    for j in jobs:
        offices = j.get("offices") or []
        loc = (j.get("office", {}) or {}).get("city") or \
              (offices[0].get("city") if offices and isinstance(offices[0], dict) else "") or \
              j.get("city") or ""
        country = (j.get("office", {}) or {}).get("country") or j.get("country") or ""
        loc_str = ", ".join([p for p in (loc, country) if p])
        jid = j.get("id") or j.get("reference") or j.get("slug")
        url = j.get("websites_urls", [{}])[0].get("url") if j.get("websites_urls") else None
        url = url or j.get("url") or f"https://www.welcometothejungle.com/en/companies/{token}/jobs/{j.get('slug','')}"
        row = build_row(company, jid, j.get("name") or j.get("title"), loc_str, url,
                        "custom", j.get("description") or "",
                        posted=j.get("published_at") or j.get("created_at"))
        if row:
            rows.append(row)
    return rows


def scrape_icims(cfg):
    """iCIMS has no public JSON API — parse the search page's job links. Best-effort:
    titles and URLs are reliable, location often needs the detail page, so rows without a
    parseable location fall through the hub gate and are dropped rather than guessed at."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    api = f"https://careers-{token}.icims.com/jobs/search?ss=1&in_iframe=1"
    r = request("GET", api)
    if r.status_code != 200:
        raise RetryableHTTP(f"icims {token} -> {r.status_code}")
    html = r.text
    for m in re.finditer(r'href="(/jobs/(\d+)/[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{4,140})', html):
        href, jid, title = m.group(1), m.group(2), clean_text(m.group(3))
        seg = re.search(r'title="([^"]*(?:, [A-Z]{2}|United States)[^"]*)"', html[m.end():m.end() + 400])
        row = build_row(company, jid, title, seg.group(1) if seg else "",
                        f"https://careers-{token}.icims.com{href}", "custom")
        if row:
            rows.append(row)
    return rows


def scrape_smartrecruiters(cfg):
    """SmartRecruiters public postings API. Identifiers are PascalCase and
    case-sensitive (AstroscaleUS) — never lowercase the token."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    r = request("GET", f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100")
    if r.status_code != 200:
        raise RetryableHTTP(f"smartrecruiters {token} -> {r.status_code}")
    for j in r.json().get("content", []):
        loc = j.get("location") or {}
        loc_str = ", ".join([p for p in [loc.get("city"), loc.get("region"), loc.get("country")] if p])
        jid = j.get("id")
        # The list endpoint carries no description, so the detail endpoint is the only
        # place the posting body exists — without it every row scores off its title alone.
        desc = ""
        d = request("GET", f"https://api.smartrecruiters.com/v1/companies/{token}/postings/{jid}")
        if d.status_code == 200:
            sections = ((d.json().get("jobAd") or {}).get("sections") or {})
            desc = " ".join(clean_text((sections.get(k) or {}).get("text", ""))
                            for k in ("companyDescription", "jobDescription", "qualifications"))
        row = build_row(company, jid, j.get("name"), loc_str,
                        f"https://jobs.smartrecruiters.com/{token}/{jid}",
                        "smartrecruiters", desc, posted=j.get("releasedDate"))
        if row:
            rows.append(row)
    return rows


def scrape_recruitee(cfg):
    """Recruitee public offers feed."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    r = request("GET", f"https://{token}.recruitee.com/api/offers/")
    if r.status_code != 200:
        raise RetryableHTTP(f"recruitee {token} -> {r.status_code}")
    for j in r.json().get("offers", []):
        loc_str = ", ".join([p for p in [j.get("city"), j.get("state_code") or j.get("country_code")] if p]) \
                  or j.get("location") or ""
        url = j.get("careers_url") or f"https://{token}.recruitee.com/o/{j.get('slug')}"
        row = build_row(company, j.get("id"), j.get("title") or j.get("position"), loc_str, url,
                        "recruitee", clean_text(j.get("description", "")), posted=j.get("created_at"))
        if row:
            rows.append(row)
    return rows


def scrape_breezy(cfg):
    """Breezy HR public board. Each posting carries its own /p/<friendly_id> apply URL."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    r = request("GET", f"https://{token}.breezy.hr/json")
    if r.status_code != 200:
        raise RetryableHTTP(f"breezy {token} -> {r.status_code}")
    data = r.json()
    for j in (data if isinstance(data, list) else []):
        loc = j.get("location") or {}
        loc_str = loc.get("name") or ", ".join([p for p in [
            loc.get("city"),
            (loc.get("state") or {}).get("name") if isinstance(loc.get("state"), dict) else loc.get("state"),
            (loc.get("country") or {}).get("name") if isinstance(loc.get("country"), dict) else loc.get("country"),
        ] if p])
        url = j.get("url") or f"https://{token}.breezy.hr/p/{j.get('friendly_id') or j.get('id')}"
        row = build_row(company, j.get("id"), j.get("name"), loc_str, url, "breezy",
                        clean_text(j.get("description", "")), posted=j.get("published_date"))
        if row:
            rows.append(row)
    return rows


def scrape_rippling(cfg):
    """Rippling ATS public board. Some tenants carry a "-careers" suffix (aalyria-careers)."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    r = request("GET", f"https://api.rippling.com/platform/api/ats/v1/board/{token}/jobs")
    if r.status_code != 200:
        raise RetryableHTTP(f"rippling {token} -> {r.status_code}")
    data = r.json()
    for j in (data if isinstance(data, list) else []):
        jid = j.get("uuid") or j.get("id")
        row = build_row(company, jid, j.get("name"),
                        (j.get("workLocation") or {}).get("label", ""),
                        j.get("url") or f"https://ats.rippling.com/{token}/jobs/{jid}",
                        "rippling", clean_text(j.get("description", "")))
        if row:
            rows.append(row)
    return rows


def scrape_pinpoint(cfg):
    """Pinpoint public postings feed — {"data": [...]}, location is a nested object."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    r = request("GET", f"https://{token}.pinpointhq.com/postings.json")
    if r.status_code != 200:
        raise RetryableHTTP(f"pinpoint {token} -> {r.status_code}")
    for j in r.json().get("data", []):
        loc = j.get("location") or {}
        loc_str = loc.get("name") or ", ".join([p for p in [loc.get("city"), loc.get("province")] if p])
        desc = " ".join(clean_text(j.get(k, "")) for k in
                        ("description", "key_responsibilities", "skills_knowledge_expertise"))
        url = j.get("url") or f"https://{token}.pinpointhq.com/en/postings/{j.get('id')}"
        row = build_row(company, j.get("id"), j.get("title"), loc_str, url, "pinpoint", desc)
        if row:
            rows.append(row)
    return rows


def scrape_manatal(cfg):
    """Manatal career-page API (careers-page.com is Manatal's hosted product).
    Paginated ten per page — follow "next" or a 191-role board truncates to its first
    page. The title field is position_name, not title."""
    company, token = cfg["company"], cfg["token"]
    rows = []
    url = f"https://api.manatal.com/open/v3/career-page/{token}/jobs/"
    guard = 0
    while url and guard < 40:
        guard += 1
        r = request("GET", url)
        if r.status_code != 200:
            if rows:
                break
            raise RetryableHTTP(f"manatal {token} -> {r.status_code}")
        payload = r.json()
        for j in payload.get("results", []):
            loc_str = j.get("location_display") or ", ".join(
                [p for p in [j.get("city"), j.get("state"), j.get("country")] if p])
            if not loc_str and j.get("is_remote"):
                loc_str = "Remote"
            row = build_row(company, j.get("hash") or j.get("id"), j.get("position_name"),
                            loc_str,
                            f"https://www.careers-page.com/{token}/job/{j.get('hash')}",
                            "manatal", clean_text(j.get("description", "")))
            if row:
                rows.append(row)
        url = payload.get("next")
    return rows


# --------------------------------------------------------------------
# Main scrub cycle
# --------------------------------------------------------------------
def build_tasks():
    tasks = []
    for token, val in GREENHOUSE.items():
        # value is either a display-name string (verified board) or
        # {"company": ..., "unverified": true} for a best-guess token.
        name = val.get("company") if isinstance(val, dict) else val
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
    for cfg in BAMBOOHR:
        tasks.append((cfg["company"], "bamboohr", lambda c=cfg: scrape_bamboohr(c)))
    for cfg in PERSONIO:
        tasks.append((cfg["company"], "personio", lambda c=cfg: scrape_personio(c)))
    for cfg in WELCOMEKIT:
        tasks.append((cfg["company"], "welcomekit", lambda c=cfg: scrape_welcomekit(c)))
    for cfg in ICIMS:
        tasks.append((cfg["company"], "icims", lambda c=cfg: scrape_icims(c)))
    for cfg in CUSTOM_HTML:
        tasks.append((cfg["company"], "custom", lambda c=cfg: scrape_custom(c)))
    for cfg in SMARTRECRUITERS:
        tasks.append((cfg["company"], "smartrecruiters", lambda c=cfg: scrape_smartrecruiters(c)))
    for cfg in RECRUITEE:
        tasks.append((cfg["company"], "recruitee", lambda c=cfg: scrape_recruitee(c)))
    for cfg in BREEZY:
        tasks.append((cfg["company"], "breezy", lambda c=cfg: scrape_breezy(c)))
    for cfg in RIPPLING:
        tasks.append((cfg["company"], "rippling", lambda c=cfg: scrape_rippling(c)))
    for cfg in PINPOINT:
        tasks.append((cfg["company"], "pinpoint", lambda c=cfg: scrape_pinpoint(c)))
    for cfg in MANATAL:
        tasks.append((cfg["company"], "manatal", lambda c=cfg: scrape_manatal(c)))
    random.shuffle(tasks)   # spread load across domains naturally
    return tasks


def execute_scrub():
    print(f"\n>>> Orbital multi-ATS scrub  ({datetime.now():%Y-%m-%d %H:%M})")
    tasks = build_tasks()
    payload, total, ok_boards = [], 0, 0
    progress_start(tasks)
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
                progress_board(source, len(rows or []))
            except Exception as exc:
                print(f"   !! {company} [{source}]: {exc}")
                log_failure(company, source, exc)
                _RUN_FAILURES.append((company, source, str(exc)[:120]))
                progress_board(source, 0, failed=True)

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
    # ---- Diagnostic summary: readable in the Actions log itself (no artifact download) ----
    by_src = {}
    for r in payload: by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    print(f"\n>>> Complete. {len(payload)} clean row(s) from {ok_boards} board(s) "
          f"upserted into '{TABLE}'.")
    print(f">>> Rows by source: {by_src or '(none)'}")
    if _RUN_FAILURES:
        print(f">>> {len(_RUN_FAILURES)} board(s) FAILED — top errors:")
        from collections import Counter
        histo = Counter(re.sub(r"https?://\S+", "<url>", e) for _, _, e in _RUN_FAILURES)
        for err, n in histo.most_common(5):
            print(f"      {n}x  {err}")
        for co, src, err in _RUN_FAILURES[:10]:
            print(f"      - {co} [{src}]: {err}")
        print(">>> Full list -> failed_scrapes_log.csv artifact")
    missing_srcs = {"workday", "amazon"} - set(by_src)
    if missing_srcs and ok_boards:
        print(f">>> WARNING: zero rows from {sorted(missing_srcs)} — those ATS families are "
              f"failing silently. Run the workflow with mode=diagnose to probe each family.")
    if ok_boards == 0:
        progress_finish("failed", 0, "every board failed")
        print(">>> FATAL: every board failed — exiting 1 so the run shows red.")
        raise SystemExit(1)
    progress_finish("done", len(payload),
                    f"{ok_boards} board(s), {len(_RUN_FAILURES)} failure(s)")


_RUN_FAILURES = []   # (company, source, error) tuples for the end-of-run summary
_SKIP_COLS = set()   # columns the live table is missing; learned once, applied to all rows

# --------------------------------------------------------------------
# Live progress telemetry
# --------------------------------------------------------------------
# The dashboard's "Refresh roles" button dispatches this workflow and then needs to
# show what is happening. GitHub's API only exposes whole-step status, so the per-ATS
# detail is written here: one scrape_runs header row, plus one scrape_progress row per
# ATS family, updated as boards finish. Every write is wrapped in try/except and can
# never fail the scrape — telemetry is not worth losing a run over. If the two tables
# don't exist yet (older schema), the first write fails once and progress goes quiet.
RUN_ID = os.environ.get("GITHUB_RUN_ID") or f"local-{int(time.time())}"
RUN_TRIGGER = os.environ.get("ORBITAL_TRIGGER") or (
    "schedule" if os.environ.get("GITHUB_EVENT_NAME") == "schedule" else "manual")
_PROGRESS_OK = True          # flipped off after the first failure so we stop retrying
_PROGRESS_LOCK = threading.Lock()
_PROGRESS = {}               # source -> {"boards_total":n,"boards_done":n,"rows":n}
_LAST_FLUSH = 0.0


def _progress_write(table, rows):
    global _PROGRESS_OK
    if not _PROGRESS_OK or not rows:
        return
    try:
        supabase.table(table).upsert(rows).execute()
    except Exception as exc:
        _PROGRESS_OK = False
        print(f"   .. progress telemetry off ({table}: {str(exc)[:80]}) — "
              f"run the scrape_runs/scrape_progress SQL from SUPABASE-SCHEMA.sql to enable it")


def progress_start(tasks):
    with _PROGRESS_LOCK:
        for _company, source, _fn in tasks:
            slot = _PROGRESS.setdefault(source, {"boards_total": 0, "boards_done": 0, "rows": 0})
            slot["boards_total"] += 1
    _progress_write("scrape_runs", [{
        "run_id": RUN_ID, "status": "running", "trigger": RUN_TRIGGER,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "boards_total": len(tasks), "boards_done": 0, "rows_upserted": 0,
    }])
    progress_flush(force=True)


def progress_board(source, row_count, failed=False):
    global _LAST_FLUSH
    with _PROGRESS_LOCK:
        slot = _PROGRESS.setdefault(source, {"boards_total": 0, "boards_done": 0, "rows": 0})
        slot["boards_done"] += 1
        slot["rows"] += 0 if failed else row_count
    # Throttled: ~90 boards finishing would otherwise mean 90 round-trips mid-scrape.
    if time.time() - _LAST_FLUSH > 2.0:
        progress_flush()


def progress_flush(force=False):
    global _LAST_FLUSH
    _LAST_FLUSH = time.time()
    with _PROGRESS_LOCK:
        snapshot = {k: dict(v) for k, v in _PROGRESS.items()}
    now = datetime.now(timezone.utc).isoformat()
    _progress_write("scrape_progress", [{
        "run_id": RUN_ID, "source": src,
        "boards_total": v["boards_total"], "boards_done": v["boards_done"],
        "rows": v["rows"], "updated_at": now,
        "status": "done" if v["boards_done"] >= v["boards_total"] else "running",
    } for src, v in snapshot.items()])
    done = sum(v["boards_done"] for v in snapshot.values())
    _progress_write("scrape_runs", [{"run_id": RUN_ID, "boards_done": done}])


def progress_finish(status, rows_upserted, note=""):
    progress_flush(force=True)
    _progress_write("scrape_runs", [{
        "run_id": RUN_ID, "status": status, "rows_upserted": rows_upserted,
        "finished_at": datetime.now(timezone.utc).isoformat(), "note": note[:400],
    }])


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


def diagnose():
    """Fast health probe: one endpoint per ATS family + Supabase read/write, PASS/FAIL
    per line, done in under a minute. Run via Actions -> Run workflow -> mode=diagnose."""
    print(">>> ORBITAL DIAGNOSE — probing one endpoint per family\n")
    checks = [
        ("greenhouse", "GET",  "https://boards-api.greenhouse.io/v1/boards/spacex/jobs", None),
        ("lever",      "GET",  "https://api.lever.co/v0/postings/kepler?mode=json&limit=1", None),
        ("ashby",      "POST", "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams",
         {"operationName": "ApiJobBoardWithTeams",
          "variables": {"organizationHostedJobsPageName": "apex.space"}, "query": ASHBY_QUERY}),
        ("workday",    "POST", "https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs",
         {"limit": 1, "offset": 0, "appliedFacets": {}}),
        # The six families added by the 2026-09-06 route passes. A family with no probe
        # here can break silently for weeks, because nothing but the row count would say so.
        ("smartrecruiters", "GET", "https://api.smartrecruiters.com/v1/companies/AstroscaleUS/postings?limit=1", None),
        ("recruitee",  "GET",  "https://aetherflux.recruitee.com/api/offers/", None),
        ("breezy",     "GET",  "https://zeno-power.breezy.hr/json", None),
        ("rippling",   "GET",  "https://api.rippling.com/platform/api/ats/v1/board/orbitfab/jobs", None),
        ("pinpoint",   "GET",  "https://astrolab.pinpointhq.com/postings.json", None),
        ("manatal",    "GET",  "https://api.manatal.com/open/v3/career-page/castelion-corporation/jobs/", None),
    ]
    failures = 0
    for fam, method, url, body in checks:
        try:
            kw = {"timeout": 15}
            if body is not None:
                kw["headers"] = {"Content-Type": "application/json", "Accept": "application/json"}
                kw["data"] = json.dumps(body)
            r = SESSION.request(method, url, **kw)
            ok = r.status_code == 200
            print(f"   {'PASS' if ok else 'FAIL'}  {fam:11s} HTTP {r.status_code}"
                  + ("" if ok else f"  <- this family is blocked/broken from this runner"))
            failures += 0 if ok else 1
        except Exception as exc:
            print(f"   FAIL  {fam:11s} {type(exc).__name__}: {str(exc)[:90]}")
            failures += 1
    try:
        supabase.table(TABLE).select("id").limit(1).execute()
        print(f"   PASS  supabase-read")
    except Exception as exc:
        print(f"   FAIL  supabase-read  {str(exc)[:110]}"); failures += 1
    try:
        supabase.table("user_state").upsert({"k": "diagnose-probe", "v": {"ts": 0}}).execute()
        print(f"   PASS  supabase-write (user_state probe row)")
    except Exception as exc:
        print(f"   WARN  supabase-write  {str(exc)[:110]}  (run the user_state SQL if not set up)")
    print(f"\n>>> Diagnose complete — {failures} hard failure(s).")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    try:
        if "--diagnose" in sys.argv:
            diagnose()
        else:
            execute_scrub()
    except SystemExit:
        raise
    except Exception:
        import traceback
        print("\n>>> CRASH — unhandled exception (this is the root cause):")
        traceback.print_exc()
        try:
            progress_finish("failed", 0, "crashed")   # so the dashboard stops saying "running"
        except Exception:
            pass
        raise SystemExit(1)
