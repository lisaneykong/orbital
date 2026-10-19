// DAILY EMAIL — 8:00 AM Central. Every role first posted by an employer in the last 24
// hours (by the job board's own posting date), plus the Apply Queue and your application
// progress. Sent through Resend to EMAIL_TO (default one@lisaney.com).
//   node daily-email.mjs            send (once per Chicago day; email_log prevents repeats)
//   node daily-email.mjs --force    send even if today's already went out
//   node daily-email.mjs --preview  build it, write out/email-preview.html, send nothing
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, SITE, requireEnv, sbSelect, sbUpsert, loadTracking, chicagoDate, chicagoLong, chicagoTime,
         HUB_LABEL, HUB_ORDER, postedMs, daysSince, isHot, esc } from './lib.mjs';

const PREVIEW = process.argv.includes('--preview');
const FORCE = process.argv.includes('--force');
requireEnv(['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']);
const TO = process.env.EMAIL_TO || 'one@lisaney.com';
const FROM = process.env.EMAIL_FROM || 'Orbital <onboarding@resend.dev>';
const MAX_ROLES = 40;
const today = chicagoDate();

// ---- once per day ----
const log = await sbSelect('email_log', `select=sent_on&sent_on=eq.${today}`);
if (log.missing) console.log('::warning::email_log table missing (run SUPABASE-APPLY-QUEUE.sql) — sending without the once-a-day guard.');
else if (log.rows.length && !FORCE && !PREVIEW) { console.log(`Today's email (${today}) already went out. Use --force to resend.`); process.exit(0); }

// ---- data ----
const since = new Date(Date.now() - 864e5).toISOString();
const { rows: fresh } = await sbSelect('jobs',
  `select=id,company,title,location,location_hub,url,match,timestamp,salary_range,is_intern,type&timestamp=gte.${since}&order=match.desc,timestamp.desc`);
const { rows: runs } = await sbSelect('scrape_runs', 'select=status,started_at,finished_at,rows_upserted&order=started_at.desc&limit=1', { page: 1, max: 1 });
const q = await sbSelect('app_queue', 'select=job_id,company,title,location,url,match,posted_at,status,prepared_at,applied_at,gaps,notes');
const tracking = await loadTracking();

const lastRun = runs[0];
const scrapeOk = lastRun && lastRun.status === 'done' && (lastRun.rows_upserted || 0) > 0
  && chicagoDate(new Date(lastRun.finished_at || lastRun.started_at)) === today;
const ready = q.rows.filter(r => r.status === 'ready').sort((a, b) => (b.match || 0) - (a.match || 0));
const readyNew = ready.filter(r => Date.parse(r.prepared_at) >= Date.now() - 864e5);
const strong = fresh.filter(j => (j.match || 0) >= 75);

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
const F = "Arial, Helvetica, sans-serif", SERIF = "Georgia, 'Times New Roman', serif", MONO = "'Courier New', Courier, monospace";
const C = { page: '#e9eef5', navy: '#0e1a2b', navy2: '#15263d', ink: '#18212f', muted: '#56657a', line: '#dde4ee', card: '#fbfcfe', cyan: '#37d6e6', link: '#1f4fa3', hot: '#c2410c', soft: '#aebbd0', head: '#f3f6fb' };
const pill = m => {
  const [bg, fg] = m >= 75 ? ['#dff3ea', '#0d6b4a'] : m >= 50 ? ['#fbeed6', '#7a4d00'] : ['#eceff4', '#4a576a'];
  return `<span style="display:inline-block;padding:4px 9px;border-radius:999px;background:${bg};color:${fg};font:700 13px/1 ${F};">${m}%</span>`;
};
const fmtDay = ms => new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', month: 'short', day: 'numeric' }).format(new Date(ms));
const ago = ms => { const d = daysSince(ms); return d == null ? 'posting date unknown' : d === 0 ? 'posted today' : d === 1 ? 'posted yesterday' : `posted ${d} days ago`; };
const section = (title, sub) => `<tr><td style="padding:30px 0 4px;"><div style="font:700 11px/1 ${MONO};letter-spacing:2px;color:${C.link};text-transform:uppercase;">${esc(title)}</div>${sub ? `<div style="font:14px/1.5 ${F};color:${C.muted};padding-top:6px;">${sub}</div>` : ''}</td></tr>`;
const button = (href, label) => `<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="${C.link}" style="border-radius:8px;"><a href="${href}" style="display:block;padding:11px 18px;font:700 14px/1 ${F};color:#fbfcfe;text-decoration:none;border-radius:8px;">${esc(label)}</a></td></tr></table>`;

const roleRow = j => {
  const hot = isHot(j);
  const meta = [j.company, j.location].filter(Boolean).map(esc).join(' &middot; ');
  const extra = [j.is_intern || j.type === 'Internship' ? 'Internship' : '', j.salary_range ? esc(j.salary_range) : ''].filter(Boolean).join(' &middot; ');
  return `<tr><td style="padding:14px 0;border-top:1px solid ${C.line};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td valign="top" style="padding-right:14px;">
        <a href="${esc(j.url || SITE)}" style="font:700 15px/1.35 ${F};color:${C.ink};text-decoration:none;">${hot ? '<span title="Hot">&#128293;</span> ' : ''}${esc(j.title)}</a>
        <div style="font:13px/1.5 ${F};color:${C.muted};padding-top:3px;">${meta}</div>
        ${extra ? `<div style="font:12px/1.5 ${F};color:${C.muted};">${extra}</div>` : ''}
      </td>
      <td valign="top" align="right" width="62" style="width:62px;white-space:nowrap;">${pill(j.match || 0)}</td>
    </tr></table></td></tr>`;
};

// ---- sections ----
let body = '';
if (!scrapeOk) {
  body += `<tr><td style="padding:22px 0 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding:12px 14px;background:#fbeed6;border-radius:8px;font:13px/1.5 ${F};color:#5c3a00;">
    <b>Today's 6 AM scrape has not finished</b>${lastRun ? ` (last run: ${esc(lastRun.status)}, ${esc(chicagoLong(new Date(lastRun.started_at)))})` : ''}. This list may be missing roles. The catch-up runs at 10 AM, 2 PM and 6 PM retry automatically.</td></tr></table></td></tr>`;
}

if (ready.length) {
  body += section('Ready to apply', `${readyNew.length ? `${readyNew.length} prepared this morning. ` : ''}Tailored résumé and cover letter are waiting in Orbital. Read them, then apply on the company site.`);
  for (const r of ready.slice(0, 8)) {
    const hard = (r.gaps || []).filter(g => g.level === 'hard').length;
    const n = r.notes || {};
    const facts = [ago(Date.parse(r.posted_at)), hard ? `${hard} hard gap${hard > 1 ? 's' : ''}` : 'no hard gaps', n.deadline ? `deadline ${esc(n.deadline)}` : ''].filter(Boolean).join(' &middot; ');
    body += `<tr><td style="padding:14px 0;border-top:1px solid ${C.line};">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td valign="top" style="padding-right:14px;">
          <div style="font:700 15px/1.35 ${F};color:${C.ink};">${esc(r.title)}</div>
          <div style="font:13px/1.5 ${F};color:${C.muted};padding-top:3px;">${esc(r.company)}${r.location ? ' &middot; ' + esc(r.location) : ''}</div>
          <div style="font:12px/1.5 ${F};color:${hard ? C.hot : C.muted};">${facts}</div>
        </td>
        <td valign="top" align="right" width="62" style="width:62px;">${pill(r.match || 0)}</td>
      </tr></table></td></tr>`;
  }
  body += `<tr><td style="padding:10px 0 0;">${button(SITE + '#view=apply', `Review ${ready.length} in the Apply Queue`)}</td></tr>`;
}

body += section('New in the last 24 hours', fresh.length
  ? `${fresh.length} role${fresh.length > 1 ? 's' : ''} first posted by the employer since yesterday morning, highest match first. &#128293; = hot.`
  : 'No roles were first posted by an employer in the last 24 hours.');
const shown = fresh.slice(0, MAX_ROLES);
for (const hub of [...HUB_ORDER, null]) {
  const group = shown.filter(j => hub ? j.location_hub === hub : !HUB_ORDER.includes(j.location_hub));
  if (!group.length) continue;
  body += `<tr><td style="padding:20px 0 6px;font:700 12px/1 ${F};color:${C.ink};">${esc(hub ? HUB_LABEL[hub] : 'Other')} <span style="color:${C.muted};font-weight:400;">&middot; ${group.length}</span></td></tr>`;
  body += group.map(roleRow).join('');
}
if (fresh.length > MAX_ROLES) body += `<tr><td style="padding:14px 0 0;font:14px/1.5 ${F};"><a href="${SITE}" style="color:${C.link};">${fresh.length - MAX_ROLES} more in Orbital &rarr;</a></td></tr>`;

body += section('Your applications', appList.length ? '' : 'Nothing marked applied yet. Mark roles applied in Orbital and they are tracked here.');
if (appList.length) {
  const stat = (n, l) => `<td width="25%" valign="top" style="width:25%;padding:10px 0;"><div style="font:700 22px/1 ${SERIF};color:${C.ink};">${n}</div><div style="font:12px/1.4 ${F};color:${C.muted};padding-top:4px;">${l}</div></td>`;
  body += `<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>${stat(week, 'applied this week')}${stat(appList.length, 'applied in total')}${stat(interviewing, 'interviewing')}${stat(offers, 'offers')}</tr></table></td></tr>`;
  if (followDue.length) {
    body += `<tr><td style="padding:12px 0 4px;font:700 13px/1.4 ${F};color:${C.ink};">Follow-ups due <span style="font-weight:400;color:${C.muted};">&middot; applied a week or more ago, no reply logged</span></td></tr>`;
    body += followDue.slice(0, 6).map(a => `<tr><td style="padding:8px 0;border-top:1px solid ${C.line};font:13px/1.5 ${F};color:${C.ink};">${esc(a.title)}<span style="color:${C.muted};"> &middot; ${esc(a.company)} &middot; applied ${fmtDay(a.at)} (${daysSince(a.at)} days)</span></td></tr>`).join('');
  }
}

const readyLine = ready.length ? ` · ${ready.length} ready to apply` : '';
const subject = `Orbital · ${fresh.length} new role${fresh.length === 1 ? '' : 's'}${strong.length ? ` · ${strong.length} at 75%+` : ''}${readyLine}`;
const top = fresh[0];
const preheader = top ? `Top match: ${top.title} at ${top.company} (${top.match}%).` : 'No new postings in the last 24 hours.';

const html = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark"><title>${esc(subject)}</title></head>
<body style="margin:0;padding:0;background:${C.page};">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;mso-hide:all;">${esc(preheader)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.page}" style="background:${C.page};"><tr><td align="center" style="padding:24px 12px;">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">
  <tr><td bgcolor="${C.navy}" style="background:${C.navy};padding:28px 32px 20px;border-radius:14px 14px 0 0;">
    <div style="font:700 11px/1 ${MONO};letter-spacing:3px;color:${C.cyan};">ORBITAL // DAILY BRIEF</div>
    <div style="font:400 28px/1.2 ${SERIF};color:${C.head};padding-top:12px;mso-line-height-rule:exactly;">${esc(chicagoLong())}</div>
    <div style="font:14px/1.5 ${F};color:${C.soft};padding-top:6px;">Roles first posted by employers in the 24 hours to 8:00 AM Central.</div>
  </td></tr>
  <tr><td bgcolor="${C.navy2}" style="background:${C.navy2};padding:18px 32px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td width="33%" style="width:33%;"><div style="font:700 26px/1 ${SERIF};color:${C.head};">${fresh.length}</div><div style="font:12px/1.4 ${F};color:${C.soft};padding-top:5px;">new roles</div></td>
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
    Sent by Orbital to ${esc(TO)} every day at 8:00 AM Central.<br>Match scores come from the scraper. Posting ages use the job board's original posting date.<br>To stop these emails, disable the "Orbital daily email" workflow in GitHub Actions.
  </td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table>
</body></html>`;

const text = [
  `ORBITAL DAILY BRIEF — ${chicagoLong()}`, '',
  `${fresh.length} new roles · ${strong.length} at 75%+ · ${ready.length} ready to apply`, '',
  ...(ready.length ? ['READY TO APPLY', ...ready.slice(0, 8).map(r => `- ${r.title} — ${r.company} (${r.match}%)`), `Review: ${SITE}#view=apply`, ''] : []),
  'NEW IN THE LAST 24 HOURS',
  ...(fresh.length ? shown.map(j => `- ${isHot(j) ? '[HOT] ' : ''}${j.title} — ${j.company}, ${j.location || ''} (${j.match}%) ${j.url || ''}`) : ['None.']),
  '', `Applied this week: ${week} · total: ${appList.length} · interviewing: ${interviewing} · offers: ${offers} · follow-ups due: ${followDue.length}`,
  '', SITE,
].join('\n');

fs.mkdirSync(path.join(ROOT, 'automation', 'out'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'automation', 'out', 'email-preview.html'), html);
console.log(`Subject: ${subject}\nRoles: ${fresh.length} · ready: ${ready.length} · apps: ${appList.length} · html ${Math.round(html.length / 1024)} KB`);
if (PREVIEW) { console.log('Preview only — wrote automation/out/email-preview.html, sent nothing.'); process.exit(0); }

if (!process.env.RESEND_API_KEY) {
  console.log('::error::RESEND_API_KEY is not set, so nothing was sent. Add it under Settings → Secrets and variables → Actions. The built email is attached to this run as "email-preview".');
  process.exit(1);
}
const r = await fetch('https://api.resend.com/emails', {
  method: 'POST',
  headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ from: FROM, to: [TO], subject, html, text }),
});
const out = await r.text();
if (!r.ok) {
  console.log(`::error::Resend refused the email (${r.status}): ${out.slice(0, 300)}`);
  if (/only send testing emails|verify a domain/i.test(out)) console.log('::error::The onboarding@resend.dev sender can only reach the email on your Resend account. Either sign up to Resend with one@lisaney.com, or verify lisaney.com in Resend and set EMAIL_FROM to e.g. "Orbital <orbital@lisaney.com>".');
  process.exit(1);
}
const id = (() => { try { return JSON.parse(out).id; } catch { return null; } })();
console.log(`Sent to ${TO} (${id || 'no id'}).`);
if (!log.missing) await sbUpsert('email_log', [{ sent_on: today, sent_at: new Date().toISOString(), roles: fresh.length, message_id: id }]);
