# Security rules

1. **`data/private/` is sacred.** NDA-protected client data lives here and is gitignored.
   - Never commit.
   - Never paste into PR descriptions, issues, comments, screenshots.
   - Never upload to public LLMs, pastebins, or diagram renderers.
   - Never include in error logs, telemetry, or analytics events.
2. **Filenames carrying `(Interno)`** or similar confidentiality markers are normalized on ingest before they enter logs.
3. **Secrets via env vars only.** No secrets in code, in commits, in screenshots. Use `.env` locally; secret manager in deployed envs.
4. **No `.env` commits.** `.env` is in `.gitignore`. `.env.example` is the only env file in git.
5. **JWT auth.** Every API call carries a Supabase JWT. Anonymous endpoints (`/api/health`) are explicit.
6. **RLS by default.** Every Supabase table has RLS enabled. Service-role access is server-side only and never exposed to the browser.
7. **No service-role key in the frontend.** Ever.
8. **Place reviews follow Google's display rules** — author attribution, source link, no editing.
9. **Uploaded files** go to Supabase Storage, never persisted inside a container image.
10. **Dependencies pinned.** Lockfiles committed. Renovate / Dependabot enabled (Phase 8).
11. **Rate-limit at the edge.** See [docs/API_SPEC.md](../../docs/API_SPEC.md) § rate limits.
12. **PII minimization.** Reviews contain author handles — treat as PII; consider hashing in derived views.
13. **No third-party tracking by default.** Analytics is opt-in only.
14. **Incident response.** Logged via Sentry + correlation IDs. Runbook (Phase 9) details rotation and disclosure.
