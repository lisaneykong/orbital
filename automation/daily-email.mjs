// DAILY EMAIL — 8:00 AM Central. Every role first posted by an employer in the last 24
// hours (by the job board's own posting date), plus the Apply Queue and your application
// progress. Sent through Resend to EMAIL_TO (default one@lisaney.com).
//   node daily-email.mjs            send (once per Chicago day; email_log prevents repeats)
//   node daily-email.mjs --force    send even if today's already went out
//   node daily-email.mjs --preview  build it, write out/email-preview.html, send nothing
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, SITE, requireEnv, sbSelect, sbUpsert, loadTracking, chicagoDate, chicagoLong, chicagoTime,
         HUB_LABEL, HUB_ORDER, postedMs, daysSince, esc } from './lib.mjs';
import { loadOrbitalFit, scoreRows } from './fit.mjs';

const PREVIEW = process.argv.includes('--preview');
const FORCE = process.argv.includes('--force');
requireEnv(['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']);
const TO = process.env.EMAIL_TO || 'one@lisaney.com';
const FROM = process.env.EMAIL_FROM || 'Orbital <onboarding@resend.dev>';
const today = chicagoDate();

// ---- once per day ----
const log = await sbSelect('email_log', `select=sent_on&sent_on=eq.${today}`);
if (log.missing && process.env.LATE_SLOT && !FORCE && !PREVIEW) {
  console.log('::warning::email_log table missing, so this later slot cannot tell whether 8am already sent. Skipping. Run SUPABASE-SCHEMA.sql.');
  process.exit(0);
}
if (log.missing) console.log('::warning::email_log table missing (run SUPABASE-SCHEMA.sql) — sending without the once-a-day guard.');
else if (log.rows.length && !FORCE && !PREVIEW) { console.log(`Today's email (${today}) already went out. Use --force to resend.`); process.exit(0); }

// ---- data ----
const since = new Date(Date.now() - 864e5).toISOString();
const { rows: freshRows } = await sbSelect('jobs', `select=*&timestamp=gte.${since}&order=match.desc,timestamp.desc`);
const { rows: runs } = await sbSelect('scrape_runs', 'select=status,started_at,finished_at,rows_upserted&order=started_at.desc&limit=1', { page: 1, max: 1 });
const q = await sbSelect('app_queue', 'select=job_id,company,title,location,url,match,posted_at,status,prepared_at,applied_at,gaps,notes');
const tracking = await loadTracking();
// Score with the dashboard's own engine (fit.mjs), so the % here is the % the dossier shows.
// Roles you dismissed or applied to are left out. Hot = heat 4-5 (75%+ fit), Lukewarm = heat 3
// (55-74%); anything weaker is counted, not listed.
const fit = loadOrbitalFit(tracking.raw);
const fresh = scoreRows(fit, freshRows.filter(r => !tracking.dismissed.has(r.id) && !tracking.applied.has(r.id)))
  .sort((a, b) => b.match - a.match);
const hot = fresh.filter(j => j.match >= 75), luke = fresh.filter(j => j.match >= 55 && j.match < 75);
const coldCount = fresh.length - hot.length - luke.length;

const lastRun = runs[0];
const scrapeOk = lastRun && lastRun.status === 'done' && (lastRun.rows_upserted || 0) > 0
  && chicagoDate(new Date(lastRun.finished_at || lastRun.started_at)) === today;
const ready = q.rows.filter(r => r.status === 'ready').sort((a, b) => (b.match || 0) - (a.match || 0));
const readyNew = ready.filter(r => Date.parse(r.prepared_at) >= Date.now() - 864e5);
const strong = hot;

// Attach the résumé and cover letter prepared this morning, so applying is: open the
// email, read the draft, upload it on the posting. Capped to keep the email small.
const ATTACH_MAX = 8;
const attachIds = readyNew.slice(0, ATTACH_MAX).map(r => r.job_id);
const attachments = [], attachedIds = new Set();
if (attachIds.length) {
  const inList = encodeURIComponent('(' + attachIds.map(id => '"' + String(id).replace(/"/g, '') + '"').join(',') + ')');
  const { rows: files } = await sbSelect('app_queue', `select=job_id,resume_file,resume_b64,cover_file,cover_b64&job_id=in.${inList}`);
  for (const f of files) {
    if (f.resume_b64) attachments.push({ filename: f.resume_file || `Resume_${f.job_id}.docx`, content: f.resume_b64 });
    if (f.cover_b64) attachments.push({ filename: f.cover_file || `CoverLetter_${f.job_id}.docx`, content: f.cover_b64 });
    if (f.resume_b64 || f.cover_b64) attachedIds.add(f.job_id);
  }
}

// applications = what you marked applied in the dashboard (synced) + anything marked
// applied from the Apply Queue that has not synced yet
const apps = new Map();
for (const id of tracking.applied) {
  const m = tracking.appliedMeta[id] || {};
  apps.set(id, { id, title: m.title || id, company: m.company || '', at: tracking.appliedDates[id] ? Date.parse(tracking.appliedDates[id]) : null, status: tracking.appStatus[id] || 'applied' });
}
for (const r of q.rows.filter(r => r.status === 'applied')) {
  if (!apps.has(r.job_id)) apps.set(r.job_id, { id: r.job_id, title: r.title, company: r.company, at: r.applied_at ? Date.parse(r.applied_at) : null, status: tracking.appStatus[r.job_id] || 'applied' });
}
const appList = [...apps.values()];
const week = appList.filter(a => a.at && a.at >= Date.now() - 7 * 864e5).length;
const interviewing = appList.filter(a => a.status === 'interview').length;
const offers = appList.filter(a => a.status === 'offer').length;
const followDue = appList.filter(a => a.at && a.status === 'applied' && !tracking.followups[a.id] && Date.now() - a.at >= 7 * 864e5)
  .sort((a, b) => a.at - b.at);

// ---- design tokens (inline everywhere; email clients drop <style>) ----
// Orbital's own brand (index.html :root): deep-space navy panels, blue→violet accent, cyan
// labels, Space Grotesk / Inter Tight / JetBrains Mono. Clients without web fonts fall back.
const F = "'Inter Tight', 'Segoe UI', Arial, sans-serif", SERIF = "'Space Grotesk', 'Segoe UI', Arial, sans-serif", MONO = "'JetBrains Mono', 'Courier New', monospace";
const C = { page: '#10161f', navy: '#18212f', navy2: '#243045', ink: '#f6faff', muted: '#b6c5d9', line: '#3b4d66', card: '#1e2839', cyan: '#37d6e6', link: '#8fb0ff', hot: '#ff6f86', soft: '#8fa0b8', head: '#f6faff', a: '#5b8cff', a2: '#9d6bff', good: '#37e0a0', gold: '#f5c560' };
const pill = m => {
  const [bg, fg] = m >= 75 ? ['#123a2e', '#37e0a0'] : m >= 50 ? ['#3a2f12', '#f5c560'] : ['#2b3950', '#b6c5d9'];
  return `<span style="display:inline-block;padding:4px 9px;border-radius:999px;background:${bg};color:${fg};font:700 13px/1 ${F};">${m}%</span>`;
};
const fmtDay = ms => new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', month: 'short', day: 'numeric' }).format(new Date(ms));
const ago = ms => { const d = daysSince(ms); return d == null ? 'posting date unknown' : d === 0 ? 'posted today' : d === 1 ? 'posted yesterday' : `posted ${d} days ago`; };
const section = (title, sub) => `<tr><td style="padding:30px 0 4px;"><div style="font:700 11px/1 ${MONO};letter-spacing:2px;color:${C.link};text-transform:uppercase;">${esc(title)}</div>${sub ? `<div style="font:14px/1.5 ${F};color:${C.muted};padding-top:6px;">${sub}</div>` : ''}</td></tr>`;
const button = (href, label) => `<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="${C.a}" style="border-radius:10px;background:${C.a};background-image:linear-gradient(90deg,${C.a},${C.a2});"><a href="${href}" style="display:block;padding:12px 20px;font:700 14px/1 ${F};color:#ffffff;text-decoration:none;border-radius:8px;">${esc(label)}</a></td></tr></table>`;

// Every role in the 24-hour list is within the 7-day "hot" window, so no flame here: it
// would mark every row and tell you nothing.
// #job=<id> opens that role's dossier in Orbital (handled after live data loads).
const appLink = id => `${SITE}#job=${encodeURIComponent(id)}`;
const links = items => `<div style="font:600 12px/1.6 ${F};padding-top:5px;">${items.filter(Boolean).map(([href, label]) =>
  `<a href="${esc(href)}" style="color:${C.link};text-decoration:none;">${label}</a>`).join(`<span style="color:${C.soft};"> &nbsp;&middot;&nbsp; </span>`)}</div>`;
const flames = n => `<span style="font:14px/1 ${F};letter-spacing:-1px;">${'&#128293;'.repeat(n)}</span>`;
const RELOC_C = { great: '#37e0a0', good: '#5ec8ff', check: '#f5c560', avoid: '#ff6f86' };
// Compact on purpose: Gmail clips an email past ~102 KB, and a busy day lists 200+ roles.
const salTxt = j => j.type === 'Internship' && !j.internRate ? 'pay not posted' : j.salary;
const flagTxt = j => (j.matchFlags || []).filter(f => !/^(Avoid|Check closely):/.test(f)).join('; ');
const relocTxt = j => j.reloc ? `<b style="color:${RELOC_C[j.reloc.tier]}">${esc(j.reloc.label)}</b>` : '';
const roleRow = j => `<tr><td style="padding:9px 0;border-top:1px solid ${C.line};font:13px/1.45 ${F};color:${C.ink}"><b>${j.match}%</b> ${flames(j.heat)} <a href="${esc(appLink(j.id))}" style="color:${C.ink};font-weight:700">${esc(j.title)}</a><br><b style="color:${C.good}">${esc(salTxt(j))}</b> &middot; ${esc(j.company)} &middot; ${esc(String(j.location).split("~")[0].slice(0,48))}${j.reloc ? ' &middot; ' + relocTxt(j) : ''}${flagTxt(j) ? `<br><span style="color:${C.hot}">&#9888; ${esc(flagTxt(j))}</span>` : ''}${j.url ? ` &middot; <a href="${esc(j.url)}" style="color:${C.link}">Apply</a>` : ''}</td></tr>`;
const lukeRow = j => `<tr><td style="padding:6px 0;border-top:1px solid ${C.line};font:12px/1.4 ${F};color:${C.muted}"><b style="color:${C.ink}">${j.match}%</b> <a href="${esc(appLink(j.id))}" style="color:${C.ink}">${esc(j.title)}</a> &middot; <b style="color:${C.good}">${esc(salTxt(j))}</b> &middot; ${esc(j.company)} &middot; ${esc(String(j.location).split("~")[0].slice(0,48))}${j.reloc ? ' &middot; ' + relocTxt(j) : ''}</td></tr>`;

// ---- sections ----
let body = '';
if (!scrapeOk) {
  body += `<tr><td style="padding:22px 0 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding:12px 14px;background:#3a2f12;border-radius:8px;font:13px/1.5 ${F};color:#f5c560;">
    <b>Today's 6 AM scrape has not finished</b>${lastRun ? ` (last run: ${esc(lastRun.status)}, ${esc(chicagoLong(new Date(lastRun.started_at)))})` : ''}. This list may be missing roles. The catch-up runs at 10 AM, 2 PM and 6 PM retry automatically.</td></tr></table></td></tr>`;
}

if (ready.length) {
  body += section('Ready to apply', `${readyNew.length ? `${readyNew.length} prepared this morning${attachments.length ? '; their résumés and cover letters are attached to this email' : ''}. ` : ''}Read each draft, then apply on the company site.`);
  for (const r of ready.slice(0, 8)) {
    const hard = (r.gaps || []).filter(g => g.level === 'hard').length;
    const n = r.notes || {};
    const facts = [attachedIds.has(r.job_id) ? '&#128206; attached' : '', ago(Date.parse(r.posted_at)), hard ? `${hard} hard gap${hard > 1 ? 's' : ''}` : 'no hard gaps', n.deadline ? `deadline ${esc(n.deadline)}` : ''].filter(Boolean).join(' &middot; ');
    body += `<tr><td style="padding:14px 0;border-top:1px solid ${C.line};">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td valign="top" style="padding-right:14px;">
          <a href="${esc(appLink(r.job_id))}" style="font:700 15px/1.35 ${F};color:${C.ink};text-decoration:none;">${esc(r.title)}</a>
          <div style="font:13px/1.5 ${F};color:${C.muted};padding-top:3px;">${esc(r.company)}${r.location ? ' &middot; ' + esc(r.location) : ''}</div>
          <div style="font:12px/1.5 ${F};color:${hard ? C.hot : C.muted};">${facts}</div>
          ${links([[appLink(r.job_id), 'Open résumé &amp; cover letter'], r.url && [r.url, 'Job posting &#8599;']])}
        </td>
        <td valign="top" align="right" width="62" style="width:62px;">${pill(r.match || 0)}</td>
      </tr></table></td></tr>`;
  }
  body += `<tr><td style="padding:10px 0 0;">${button(SITE + '#view=apply', `Review ${ready.length} in the Apply Queue`)}</td></tr>`;
}

const group = (title, sub, list, row) => {
  body += section(title, sub);
  if (!list.length) { body += `<tr><td style="padding:8px 0;font:13px/1.5 ${F};color:${C.muted};">None today.</td></tr>`; return; }
  body += list.map(row).join('');
};
group(`Hot · ${hot.length}`, 'Posted in the last 24 hours and a 75%+ fit by the same score Orbital shows (4–5 flames).', hot, roleRow);
const LUKE_PREVIEW = 5;
group(`Lukewarm · ${luke.length}`, `55–74% fit (3 flames). The top ${Math.min(LUKE_PREVIEW, luke.length)} are below; the full list is in Orbital.`, luke.slice(0, LUKE_PREVIEW), lukeRow);
if (luke.length > LUKE_PREVIEW) body += `<tr><td style="padding:10px 0 0;">${button(SITE, `See all ${luke.length} lukewarm roles in Orbital`)}</td></tr>`;
body += `<tr><td style="padding:12px 0 0;font:12px/1.5 ${F};color:${C.muted};">${coldCount} more new role${coldCount === 1 ? '' : 's'} scored under 55% and ${coldCount === 1 ? 'is' : 'are'} not listed${tracking.dismissed.size ? '; roles you skipped or applied to are left out' : ''}. Salaries marked est. are Orbital estimates; the rest are the employer's posted range.</td></tr>`;

body += section('Your applications', appList.length ? '' : 'Nothing marked applied yet. Mark roles applied in Orbital and they are tracked here.');
if (appList.length) {
  const stat = (n, l) => `<td width="25%" valign="top" style="width:25%;padding:10px 0;"><div style="font:700 22px/1 ${SERIF};color:${C.ink};">${n}</div><div style="font:12px/1.4 ${F};color:${C.muted};padding-top:4px;">${l}</div></td>`;
  body += `<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>${stat(week, 'applied this week')}${stat(appList.length, 'applied in total')}${stat(interviewing, 'interviewing')}${stat(offers, 'offers')}</tr></table></td></tr>`;
  if (followDue.length) {
    body += `<tr><td style="padding:12px 0 4px;font:700 13px/1.4 ${F};color:${C.ink};">Follow-ups due <span style="font-weight:400;color:${C.muted};">&middot; applied a week or more ago, no reply logged</span></td></tr>`;
    body += followDue.slice(0, 6).map(a => `<tr><td style="padding:8px 0;border-top:1px solid ${C.line};font:13px/1.5 ${F};color:${C.ink};"><a href="${esc(appLink(a.id))}" style="color:${C.ink};">${esc(a.title)}</a><span style="color:${C.muted};"> &middot; ${esc(a.company)} &middot; applied ${fmtDay(a.at)} (${daysSince(a.at)} days)</span></td></tr>`).join('');
  }
}

const readyLine = ready.length ? ` · ${ready.length} ready to apply` : '';
const subject = `Orbital · ${hot.length} hot · ${luke.length} lukewarm${readyLine}`;
const top = hot[0] || luke[0];
const preheader = top ? `Top match: ${top.title} at ${top.company} (${top.match}%, ${top.salary}).` : 'No new postings in the last 24 hours.';

const html = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><meta name="supported-color-schemes" content="dark"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Inter+Tight:wght@400;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet"><title>${esc(subject)}</title></head>
<body style="margin:0;padding:0;background:${C.page};">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;mso-hide:all;">${esc(preheader)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.page}" style="background:${C.page};"><tr><td align="center" style="padding:24px 12px;">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">
  <tr><td height="4" bgcolor="${C.a}" style="height:4px;line-height:4px;font-size:0;background:${C.a};background-image:linear-gradient(90deg,${C.a},${C.a2},${C.cyan});border-radius:14px 14px 0 0;">&nbsp;</td></tr>
  <tr><td bgcolor="${C.navy}" style="background:${C.navy};padding:24px 32px 20px;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td valign="middle" style="padding-right:10px;"><img src="${SITE}assets/icon-192.png" width="34" height="34" alt="Orbital" style="display:block;border:0;border-radius:9px;"></td>
      <td valign="middle" style="font:700 18px/1 ${SERIF};color:${C.head};letter-spacing:.5px;">Orbital <span style="font:500 10px/1 ${MONO};letter-spacing:3px;color:${C.cyan};padding-left:6px;">DAILY BRIEF</span></td>
    </tr></table>
    <div style="font:700 28px/1.2 ${SERIF};color:${C.head};padding-top:12px;mso-line-height-rule:exactly;">${esc(chicagoLong())}</div>
    <div style="font:14px/1.5 ${F};color:${C.soft};padding-top:6px;">Roles first posted by employers in the 24 hours to 8:00 AM Central.</div>
  </td></tr>
  <tr><td bgcolor="${C.navy2}" style="background:${C.navy2};padding:18px 32px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td width="33%" style="width:33%;"><div style="font:700 26px/1 ${SERIF};color:${C.head};">${hot.length + luke.length}</div><div style="font:12px/1.4 ${F};color:${C.soft};padding-top:5px;">new roles (55%+ fit)</div></td>
      <td width="33%" style="width:33%;"><div style="font:700 26px/1 ${SERIF};color:${C.head};">${strong.length}</div><div style="font:12px/1.4 ${F};color:${C.soft};padding-top:5px;">at 75%+ match</div></td>
      <td width="34%" style="width:34%;"><div style="font:700 26px/1 ${SERIF};color:${C.head};">${ready.length}</div><div style="font:12px/1.4 ${F};color:${C.soft};padding-top:5px;">ready to apply</div></td>
    </tr></table>
  </td></tr>
  <tr><td bgcolor="${C.card}" style="background:${C.card};padding:0 32px 30px;border-radius:0 0 14px 14px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${body}
      <tr><td style="padding:28px 0 0;">${button(SITE, 'Open Orbital')}</td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:18px 32px;font:12px/1.6 ${F};color:${C.muted};text-align:center;">
    Sent by Orbital to ${esc(TO)} every day at 8:00 AM Central.<br>Match scores are Orbital's own fit score, the same number the dashboard shows. Posting ages use the job board's original posting date.<br>To stop these emails, disable the "Orbital daily email" workflow in GitHub Actions.
  </td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table>
</body></html>`;

const text = [
  `ORBITAL DAILY BRIEF — ${chicagoLong()}`, '',
  `${hot.length} hot · ${luke.length} lukewarm · ${ready.length} ready to apply`, '',
  ...(ready.length ? ['READY TO APPLY', ...ready.slice(0, 8).map(r => `- ${r.title} — ${r.company} (${r.match}%)`), `Review: ${SITE}#view=apply`, ''] : []),
  `HOT (${hot.length})`, ...hot.map(j => `- ${j.title} — ${j.salary} — ${j.match}% — ${j.company}, ${j.location || ''} ${j.url || ''}`),
  '', `LUKEWARM (${luke.length}, top 5)`, ...luke.slice(0, 5).map(j => `- ${j.title} — ${j.salary} — ${j.match}% — ${j.company}, ${j.location || ''} ${j.url || ''}`),
  '', `Applied this week: ${week} · total: ${appList.length} · interviewing: ${interviewing} · offers: ${offers} · follow-ups due: ${followDue.length}`,
  '', SITE,
].join('\n');

fs.mkdirSync(path.join(ROOT, 'automation', 'out'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'automation', 'out', 'email-preview.html'), html);
console.log(`Subject: ${subject}\nRoles: ${fresh.length} · ready: ${ready.length} · apps: ${appList.length} · attachments: ${attachments.length} · html ${Math.round(html.length / 1024)} KB`);
if (PREVIEW) { console.log('::notice::Preview only — nothing was sent. The email is attached to this run as "email-preview". Run again with mode "send" to send it.'); process.exit(0); }

if (!process.env.RESEND_API_KEY) {
  console.log('::error::RESEND_API_KEY is not set, so nothing was sent. Add it under Settings → Secrets and variables → Actions. The built email is attached to this run as "email-preview".');
  process.exit(1);
}
const r = await fetch('https://api.resend.com/emails', {
  method: 'POST',
  headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ from: FROM, to: [TO], subject, html, text, ...(attachments.length ? { attachments } : {}) }),
});
const out = await r.text();
if (!r.ok) {
  console.log(`::error::Resend refused the email (${r.status}): ${out.slice(0, 300)}`);
  if (/only send testing emails|verify a domain/i.test(out)) console.log('::error::The onboarding@resend.dev sender can only reach the email on your Resend account. Either sign up to Resend with one@lisaney.com, or verify lisaney.com in Resend and set EMAIL_FROM to e.g. "Orbital <orbital@lisaney.com>".');
  process.exit(1);
}
const id = (() => { try { return JSON.parse(out).id; } catch { return null; } })();
console.log(`::notice::Sent to ${TO} (Resend id ${id || 'none'}). If it is not in the inbox, check spam.`);
if (!log.missing) await sbUpsert('email_log', [{ sent_on: today, sent_at: new Date().toISOString(), roles: fresh.length, message_id: id }]);
