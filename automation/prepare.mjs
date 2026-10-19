// AUTO-PREPARE — runs right after the 6am scrape.
// For every hot role (first posted by the employer within 7 days) at PREP_MIN_MATCH% or
// better that is not already queued, applied or dismissed, it builds a tailored résumé
// and a cover letter with the same engine as the dashboard's buttons, and files them in
// the app_queue table as "ready". It never submits anything: you review and apply.
import * as docx from 'docx';
import { requireEnv, sbSelect, sbUpsert, loadTracking, loadOrbitalCore, claude, postedMs, daysSince, HOT_DAYS } from './lib.mjs';

requireEnv(['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'ANTHROPIC_API_KEY']);
const MIN_MATCH = +process.env.PREP_MIN_MATCH || 75;
const MAX_PER_RUN = +process.env.PREP_MAX || 10;

const queue = await sbSelect('app_queue', 'select=job_id');
if (queue.missing) {
  console.log('::warning::The app_queue table does not exist. Run SUPABASE-APPLY-QUEUE.sql in the Supabase SQL Editor, then auto-prepare starts on the next run.');
  process.exit(0);
}
const queued = new Set(queue.rows.map(r => r.job_id));
const tracking = await loadTracking();

const since = new Date(Date.now() - HOT_DAYS * 864e5).toISOString();
const { rows: jobs } = await sbSelect('jobs',
  `select=*&timestamp=gte.${since}&match=gte.${MIN_MATCH}&archived=is.false&order=match.desc,timestamp.desc`);

const todo = jobs.filter(j => !queued.has(j.id) && !tracking.applied.has(j.id) && !tracking.dismissed.has(j.id));
console.log(`Hot roles (posted ≤${HOT_DAYS}d) at ${MIN_MATCH}%+ match: ${jobs.length}. New to prepare: ${todo.length}. This run prepares up to ${MAX_PER_RUN}.`);
if (!todo.length) process.exit(0);

const extra = (Array.isArray(tracking.resumeLibrary) ? tracking.resumeLibrary : []).filter(r => r && !r.builtin);
const core = loadOrbitalCore(docx, extra);

// Same master the browser uses: your edited copy from My Profile if you saved one,
// otherwise the seed in index.html. Library keys are backfilled, and Siemens NX flips
// to "completed" once its end date has passed.
let master = tracking.masterResume || core.ORBITAL_MASTER_RESUME;
['projectLibrary', 'skillPool', 'roleRouting'].forEach(k => { if (master[k] === undefined && core.ORBITAL_MASTER_RESUME[k] !== undefined) master[k] = core.ORBITAL_MASTER_RESUME[k]; });
if (Date.now() > Date.parse('2027-01-31T23:59:59')) {
  master = JSON.parse(JSON.stringify(master).split('Siemens NX CAD training through the program, in progress').join('Siemens NX CAD training through the program, completed January 2027'));
}

const support = extra.length
  ? '\n\nSUPPORTING RÉSUMÉS (' + extra.length + '):\n' + extra.map((r, i) => `--- ${i + 1}. ${r.name} ---\nSkills: ${(r.skills || []).join(', ')}${r.text ? '\nText: ' + String(r.text).slice(0, Math.floor(14000 / extra.length)) : ''}`).join('\n\n')
  : '';
const parseJSON = t => {
  t = String(t || '').replace(/```json|```/g, '').trim();
  const a = t.indexOf('{'), b = t.lastIndexOf('}');
  return JSON.parse(a >= 0 && b > a ? t.slice(a, b + 1) : t);
};

let done = 0, failed = 0;
for (const j of todo.slice(0, MAX_PER_RUN)) {
  const label = `${j.company} — ${j.title}`;
  try {
    const posting = `${j.title} at ${j.company}\nLocation: ${j.location || j.location_hub || ''}\n\n${(j.description || '').slice(0, 6000)}\n\n${(j.requirements || '').slice(0, 3000)}`;

    const delta = parseJSON(await claude(core.RESUME_TAILOR_RULES,
      `MASTER RÉSUMÉ JSON:\n${JSON.stringify(master)}${support}\n\nJOB POSTING:\n"""${posting}"""`, 3000));
    const tailored = core.mergeTailoring(master, delta);
    const report = core.mergeTailoring.lastReport || {};
    const resumeBuf = await docx.Packer.toBuffer(core.buildResumeDoc(tailored));

    const letter = await claude(core.COVER_LETTER_RULES,
      `MASTER RÉSUMÉ JSON:\n${JSON.stringify(master)}\n\nJOB POSTING:\n"""${posting}"""`, 1600);
    const paras = core.coverLetterParas(letter);
    if (!paras.length) throw new Error('cover letter came back empty');
    const jobForLetter = { company: j.company, title: j.title, location: j.location || '', reqId: null };
    const coverBuf = await docx.Packer.toBuffer(core.buildCoverLetterDoc(master, jobForLetter, paras));

    const stem = `${core.pascal(j.company)}_${core.pascal(j.title)}`;
    const words = paras.join(' ').split(/\s+/).filter(Boolean).length;
    await sbUpsert('app_queue', [{
      job_id: j.id, company: j.company, title: j.title, location: j.location, location_hub: j.location_hub,
      url: j.url, match: j.match, posted_at: j.timestamp, salary_range: j.salary_range, is_intern: !!j.is_intern,
      status: 'ready', prepared_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      resume_file: `Kong_Resume_${stem}.docx`, resume_b64: resumeBuf.toString('base64'),
      cover_file: `Kong_CoverLetter_${stem}.docx`, cover_b64: coverBuf.toString('base64'), cover_text: paras.join('\n\n'),
      gaps: delta.gaps || [], notes: delta.notes || {},
      checks: { salesWords: report.salesWords || [], newNumbers: report.newNumbers || [], droppedSkills: report.dropped || [],
                anchorsAdded: report.added || [], projects: report.projects || [], coverWords: words,
                coverSlots: (paras.join(' ').match(/\[[^\]]+\]/g) || []).length },
      error: null,
    }]);
    done++;
    console.log(`  ✓ ${label}  (${j.match}% · posted ${daysSince(postedMs(j))}d ago · ${(delta.gaps || []).length} gaps)`);
  } catch (e) {
    failed++;
    console.log(`  ✗ ${label}: ${e.message}`);
    if (e.fatal) {
      console.log('::error::The Anthropic API refused the key or the account is out of credits. Fix it at console.anthropic.com → Plans & Billing, then the next run picks up where this one stopped.');
      break;
    }
  }
}
console.log(`Prepared ${done}, failed ${failed}. Anything not prepared is retried on the next run.`);
if (failed && !done) process.exit(1);
