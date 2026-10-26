// Shared helpers for the GitHub Actions automation (auto-prepare + daily email).
// Reads/writes Supabase over its REST API with the service key — the same two secrets
// the scraper already uses. No npm dependencies here, so the email job needs no install.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const SITE = 'https://jobs.lisaney.com/';

const SB_URL = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const SB_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

export function requireEnv(names) {
  const missing = names.filter(n => !process.env[n]);
  if (missing.length) {
    console.log(`::error::Missing repo secret(s): ${missing.join(', ')} — Settings → Secrets and variables → Actions.`);
    process.exit(1);
  }
}

function sbHeaders(extra = {}) {
  return { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, 'Content-Type': 'application/json', ...extra };
}

// GET rows. `query` is a PostgREST query string (select=…&col=op.value&order=…).
// Returns { rows, missing } — missing=true when the table does not exist yet.
export async function sbSelect(table, query, { page = 1000, max = 20000 } = {}) {
  const rows = [];
  for (let from = 0; from < max; from += page) {
    const r = await fetch(`${SB_URL}/rest/v1/${table}?${query}`, {
      headers: sbHeaders({ Range: `${from}-${from + page - 1}`, 'Range-Unit': 'items' }),
    });
    const body = await r.text();
    if (r.status === 404 || /PGRST20\d|42P01/.test(body)) return { rows: [], missing: true };
    if (!r.ok) throw new Error(`Supabase ${table} ${r.status}: ${body.slice(0, 200)}`);
    const data = JSON.parse(body || '[]');
    rows.push(...data);
    if (data.length < page) break;
  }
  return { rows, missing: false };
}

export async function sbUpsert(table, rows) {
  const r = await fetch(`${SB_URL}/rest/v1/${table}`, {
    method: 'POST',
    headers: sbHeaders({ Prefer: 'resolution=merge-duplicates,return=minimal' }),
    body: JSON.stringify(rows),
  });
  if (!r.ok) throw new Error(`Supabase upsert ${table} ${r.status}: ${(await r.text()).slice(0, 300)}`);
}

// The dashboard syncs everything the user authors into user_state (k='tracking') as a map
// of localStorage keys → JSON strings. Parse the ones the automation needs.
export async function loadTracking() {
  try {
    const { rows } = await sbSelect('user_state', 'select=v&k=eq.tracking');
    const v = (rows[0] && rows[0].v) || {};
    const parse = (k, d) => { try { return v[k] != null ? JSON.parse(v[k]) : d; } catch { return d; } };
    return {
      raw: v,
      applied: new Set(parse('orbital.applied', [])),
      dismissed: new Set(parse('orbital.dismissed', [])),
      appliedMeta: parse('orbital.appliedMeta', {}),
      appliedDates: parse('orbital.appliedDates', {}),
      appStatus: parse('orbital.appStatus', {}),
      followups: parse('orbital.followups', {}),
      masterResume: parse('orbital.masterResume', null),
      resumeLibrary: parse('orbital.resumeLibrary', []),
    };
  } catch (e) {
    console.log(`::warning::Could not read user_state (${e.message}). Continuing without your saved tracking.`);
    return { raw: {}, applied: new Set(), dismissed: new Set(), appliedMeta: {}, appliedDates: {}, appStatus: {}, followups: {}, masterResume: null, resumeLibrary: [] };
  }
}

// Chicago wall-clock helpers (the schedule and the email are both in Central time).
export function chicagoDate(d = new Date()) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
}
export function chicagoLong(d = new Date()) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(d);
}
export function chicagoTime(d) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', hour: 'numeric', minute: '2-digit' }).format(d);
}

export const HUB_LABEL = { SEATTLE: 'Seattle', GREATER_LA: 'Greater Los Angeles', NEW_ZEALAND: 'New Zealand', US_OTHER: 'US — Other', INTERNATIONAL: 'International' };
export const HUB_ORDER = ['SEATTLE', 'GREATER_LA', 'US_OTHER', 'NEW_ZEALAND', 'INTERNATIONAL'];
export const HOT_DAYS = 7;   // hot = posted in the last 7 days (same rule as index.html isHot)

export function postedMs(j) { const t = Date.parse(j.timestamp || ''); return isNaN(t) ? null : t; }
export function daysSince(ms) { return ms == null ? null : Math.max(0, Math.floor((Date.now() - ms) / 864e5)); }
export function isHot(j) { const d = daysSince(postedMs(j)); return d != null && d <= HOT_DAYS; }

// Pull the résumé + cover-letter engine straight out of index.html, so the documents the
// morning job builds are byte-for-byte the same as the browser's Tailored Résumé button:
// same layout constants, same tailoring rules, same merge guards. One source of truth.
export function loadOrbitalCore(docx, resumeLibrary = []) {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const cut = (a, b) => {
    const i = html.indexOf(a), k = html.indexOf(b, i);
    if (i < 0 || k < 0) throw new Error(`index.html is missing the block starting "${a}"`);
    return html.slice(i, k);
  };
  const master = cut('const ORBITAL_MASTER_RESUME = ', 'function nxTense');
  const engine = cut('/* ---------- 2. LAYOUT CONSTANTS', '/* ---------- 4. AI CALL');
  const pascal = (html.match(/function pascal\(s\)\{[\s\S]*?\n\}/) || [])[0];
  const cover = cut('const COVER_LETTER_RULES = `', 'async function generateCoverLetter');
  if (!pascal) throw new Error('index.html is missing pascal()');
  const src = `${master}\n${engine}\n${pascal}\n${cover}\n
    return { ORBITAL_MASTER_RESUME, RZ, buildResumeDoc, RESUME_TAILOR_RULES, mergeTailoring, pascal, COVER_LETTER_RULES, coverLetterParas, buildCoverLetterDoc };`;
  return new Function('docx', 'resumeLibrary', src)(docx, () => resumeLibrary);
}

// Rate limits, overloads and dropped connections are retried (3 attempts, honouring
// retry-after). A bad key or an empty credit balance is fatal: retrying cannot fix it.
export async function claude(system, user, maxTokens) {
  let last;
  for (let attempt = 1; attempt <= 3; attempt++) {
    let r, body;
    try {
      r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01' },
        body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: maxTokens, system, messages: [{ role: 'user', content: user }] }),
      });
      body = await r.text();
    } catch (e) {
      last = new Error(`Anthropic API unreachable: ${e.message}`);
    }
    if (r && r.ok) return (JSON.parse(body).content || []).map(c => c.text || '').join('\n');
    if (r) {
      last = new Error(`Anthropic API ${r.status}: ${body.slice(0, 240)}`);
      last.fatal = r.status === 401 || r.status === 403 || /credit balance|billing/i.test(body);
      if (last.fatal || !(r.status === 429 || r.status >= 500)) throw last;
    }
    if (attempt < 3) {
      const ra = r ? parseFloat(r.headers.get('retry-after') || '0') : 0;
      await new Promise(res => setTimeout(res, Math.min(30000, ra > 0 ? ra * 1000 : 2000 * 2 ** (attempt - 1))));
    }
  }
  throw last;
}

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
