---
name: prepare-deployment
description: Prepare the app for deployment to staging or production. Verifies Dockerfiles, compose, env, migrations, health checks, secrets, observability, and runbook readiness. Use before any release tag.
---

# prepare-deployment

## When to use

- About to cut a release tag.
- Promoting from staging to production.
- A first-time deploy to a new environment.

## Checklist

1. **Compose sanity.** `docker compose -f docker-compose.yml config` validates. No `postgres` service (Supabase handles it).
2. **Dockerfiles.** Multi-stage, non-root user in runtime, healthchecks set.
3. **`.dockerignore`.** Excludes `data/private/`, `.env`, `.git`, `node_modules`, `.venv`.
4. **Pinned base images.** Specific tags / digests.
5. **`.env.example` in sync** with code. No new var used in code without an entry here.
6. **Secrets present** in the target environment's secret manager. No secret in compose or git.
7. **Migrations.** `supabase db push` (or equivalent) plan is reviewed. Backwards-compatible migrations preferred.
8. **Health endpoints.** `GET /api/health` returns `ok` for `supabase` and `redis`. Smoke test pre-rollout.
9. **Observability.** Sentry DSN set, OTLP endpoint configured, parser / Places / LLM dashboards reachable.
10. **Quota guard.** Google Maps API key has a daily quota cap. Pytrends scheduler enabled.
11. **Rate limits.** Configured per [docs/API_SPEC.md](../../../docs/API_SPEC.md).
12. **Rollback plan.** Previous image tag known. DB migrations are reversible or have an explicit forward-only ADR.
13. **Spanish UI verified.** No English strings in the build artifact.
14. **Verifier flag rate** on the smoke prompt set < 1%.
15. **Backup.** Most recent Supabase backup timestamp checked.

## Refusal cases

- A release that bakes secrets into an image → refuse.
- A migration without rollback or forward-only ADR → refuse.
- A release where the verifier flag rate exceeds threshold → refuse.

## Output shape

A pass/fail checklist, with a single "release readiness: GO/NO-GO" verdict at the end.
