// ORBITAL — trigger-scrape
// ============================================================================
// WHAT THIS IS FOR
// The dashboard's "Refresh roles" button needs to ask GitHub to run the scrape
// workflow. GitHub requires a token with actions:write to do that, and a static
// site has nowhere private to keep one — anything in the page is public.
//
// This function is that private place. The token lives in Supabase's secret
// store, never in the browser. The page calls this function with the public
// anon key; the function calls GitHub with the real token.
//
// DEPLOY (one time, ~2 minutes):
//   1. Install the CLI:            npm i -g supabase
//   2. Log in and link:            supabase login && supabase link --project-ref <your-ref>
//   3. Set the three secrets:      supabase secrets set GITHUB_TOKEN=ghp_xxx \
//                                    GITHUB_REPO=yourname/orbital ORBITAL_PIN=1725
//   4. Deploy:                     supabase functions deploy trigger-scrape
//
// The GitHub token needs exactly one permission: Actions -> Read and write, on
// the one repo that holds this project. Nothing else. Make it a fine-grained
// token so it can never touch anything but that repo's workflows.
//
// If this function is not deployed, the dashboard falls back to a token you
// paste into owner settings, which is stored only in that browser.
// ============================================================================

const GITHUB_TOKEN = Deno.env.get("GITHUB_TOKEN") ?? "";
const GITHUB_REPO = Deno.env.get("GITHUB_REPO") ?? "";       // "owner/repo"
const WORKFLOW = Deno.env.get("GITHUB_WORKFLOW") ?? "scrape.yml";
const BRANCH = Deno.env.get("GITHUB_BRANCH") ?? "main";
const ORBITAL_PIN = Deno.env.get("ORBITAL_PIN") ?? "";        // optional extra gate

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  // Plain-English config errors: a 500 with no explanation is the worst possible
  // outcome for someone following the setup wizard.
  if (!GITHUB_TOKEN) {
    return json({ error: "GITHUB_TOKEN secret is not set on this function. Run: supabase secrets set GITHUB_TOKEN=..." }, 500);
  }
  if (!GITHUB_REPO.includes("/")) {
    return json({ error: `GITHUB_REPO must look like owner/repo. Currently: "${GITHUB_REPO}"` }, 500);
  }

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* empty body is fine */ }

  // Optional shared-secret gate, so a stranger with the public anon key cannot
  // burn your Actions minutes. Skipped entirely when ORBITAL_PIN is unset.
  if (ORBITAL_PIN && String(body.pin ?? "") !== ORBITAL_PIN) {
    return json({ error: "Wrong or missing owner PIN." }, 403);
  }

  const mode = body.mode === "diagnose" ? "diagnose" : "full";

  const dispatch = await fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: BRANCH, inputs: { mode } }),
    },
  );

  if (dispatch.status !== 204) {
    const detail = await dispatch.text();
    const hint = dispatch.status === 404
      ? `Not found. Check GITHUB_REPO ("${GITHUB_REPO}"), that ${WORKFLOW} exists on branch "${BRANCH}", and that the token can see this repo.`
      : dispatch.status === 403
      ? "Forbidden. The token is missing the Actions: Read and write permission."
      : detail.slice(0, 300);
    return json({ error: `GitHub refused the request (HTTP ${dispatch.status}). ${hint}` }, 502);
  }

  // GitHub's dispatch endpoint returns no run id, so report the newest run for
  // this workflow — the dashboard uses it only as a starting point for polling.
  let runId: number | null = null;
  let runUrl: string | null = null;
  try {
    await new Promise((r) => setTimeout(r, 1500));   // let GitHub register the run
    const runs = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW}/runs?per_page=1`,
      { headers: { Authorization: `Bearer ${GITHUB_TOKEN}`, Accept: "application/vnd.github+json" } },
    );
    const data = await runs.json();
    runId = data?.workflow_runs?.[0]?.id ?? null;
    runUrl = data?.workflow_runs?.[0]?.html_url ?? null;
  } catch { /* polling scrape_runs works without this */ }

  return json({ ok: true, mode, run_id: runId, run_url: runUrl, dispatched_at: new Date().toISOString() });
});
