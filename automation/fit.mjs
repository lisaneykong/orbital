// The dashboard's own fit engine, run server-side. The scraper's `match` column is only the
// raw keyword score; the dashboard re-scores every role with enhanceMatch() (skill evidence,
// seniority, dealbreakers, relocation fit, ERAU credentials, your "not a match" history).
// The email and auto-prepare used to rank by the raw score, so a role sold as 80% opened in
// Orbital as a weak fit. This lifts the same code out of index.html and runs it against your
// synced settings (user_state.tracking), so every number matches what the dashboard shows.
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './lib.mjs';

function memoryStorage(seed) {
  const m = new Map(Object.entries(seed).filter(([, v]) => typeof v === 'string'));
  return {
    getItem: k => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => { m.set(k, String(v)); },
    removeItem: k => { m.delete(k); },
  };
}

// trackingRaw: the user_state 'tracking' row (localStorage keys → string values).
export function loadOrbitalFit(trackingRaw = {}) {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const cut = (a, b) => {
    const i = html.indexOf(a), k = html.indexOf(b, i);
    if (i < 0 || k < 0) throw new Error(`index.html is missing the block starting "${a}"`);
    return html.slice(i, k);
  };
  const blocks = [
    cut('const OWNER = {', '// Real coordinates for a live weather comparison'),    // profile → enhanceMatch()
    cut('const NOT_MATCH_REASONS = [', 'function notMatchSheet('),                   // rejection learning
    cut('function money(n){', 'function heatTip('),                                    // salary, posting age, heat
    cut('function hubToRegion(r){', 'const NAV=['),                                    // live row → job
    cut('const ARCHETYPES={', 'function skillsMatch(j){'),                            // role archetypes, evidence tiers
  ];
  // The browser seeds the bundled résumé once, then lets your synced profile win. That
  // seed marker is device-local, so set it here or the seed would overwrite your profile.
  const seedVersion = (html.match(/const PROFILE_SEED_VERSION='([^']+)'/) || [])[1];
  const store = memoryStorage({ ...trackingRaw, ...(seedVersion ? { 'orbital.profileSeed': seedVersion } : {}) });
  const src = `let liveClosed=new Set(); const ROLE_WINDOW_DAYS=45;\n${blocks.join('\n')}\n
    return { mapLiveJob, enhanceMatch, heatLevel, HEAT_FORMS, salaryLabel, salaryValue, relocationFit, isHot, daysOnMarket, matchIcon:
      p=>p>=85?'strong':p>=70?'decent':p>=55?'marginal':'weak', erauCredLabel: k=>ERAU_CREDS[k]&&ERAU_CREDS[k].label, OWNER };`;
  return new Function('localStorage', src)(store);
}

// Score live rows exactly as the dashboard does. Returns the mapped job objects.
export function scoreRows(fit, rows) {
  return rows.map(r => {
    const j = fit.enhanceMatch(fit.mapLiveJob(r));
    j.heat = fit.heatLevel(j);
    j.salary = fit.salaryLabel(j);
    j.reloc = fit.relocationFit(j);
    j.rawMatch = r.match;
    j.hub = r.location_hub;
    j.row = r;
    return j;
  });
}
