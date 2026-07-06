/* ============================================================
   ORBITAL — site-wide config  (OPTIONAL but recommended)
   ============================================================
   Fill these in to make jobs.lisaney.com work on EVERY device
   (phone, tablet, any browser) WITHOUT re-running setup each time.

   These are the SAME two public values from setup Step 1:
     • url     = your Supabase Project URL   (https://xxxx.supabase.co)
     • anonKey = your Supabase  anon public  key  (the READ-only one)

   Both are safe to ship publicly — the anon key can only READ jobs,
   and editing is still gated behind your owner PIN (1725).
   Do NOT put the service_role key here.

   After filling these in, re-deploy (push to GitHub → auto-publish).
   Leave them blank to keep the per-device setup flow instead.
   ============================================================ */
window.ORBITAL_CONFIG = {
  url:     "https://sgjzwyyhjlfpleaclata.supabase.co",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNnanp3eXloamxmcGxlYWNsYXRhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE3NDY1NzEsImV4cCI6MjA5NzMyMjU3MX0.fjxGm2vH4vJ5iMU8IC-pdwck7zgzzEDEdSvl0j7aprY"
};
