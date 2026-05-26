# Deployment

## 1. Environments

| Env | Purpose | URL pattern |
|---|---|---|
| `development` | local docker compose | `http://localhost:3000` |
| `staging` | shared pre-prod for the RGA team | `staging.rga.<tld>` |
| `production` | NAMA + onboarded clients | `app.rga.<tld>` |

Switch by setting `APP_ENV` and pointing at the matching Supabase project + API key set.

## 2. Components and where they run

| Component | Where |
|---|---|
| `api`, `worker`, `scheduler` | Docker containers (see `docker-compose.yml`) on a single VM or container platform |
| `web` (Next.js) | Same compose, or Vercel — TBD (see DECISIONS) |
| Postgres + Auth + Storage | **Supabase managed** — never self-hosted |
| Redis | container in compose |
| Object storage for uploads | Supabase Storage |
| Secrets | environment variables sourced from a secret manager; never in git |

## 3. Local dev

```
cp .env.example .env
# fill in keys
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Phase 0 note: the Dockerfiles referenced do not exist yet. `docker compose build` will fail until Phase 1+. The compose files are scaffolds documenting the **intended** topology.

## 4. Staging

- Promote on every merge to `main` after CI green.
- Migrations run as a pre-deploy step against the staging Supabase project.
- Smoke tests hit `/api/health` and a synthetic upload of an anonymized fixture.

## 5. Production

- Manual promotion from staging via a tagged release.
- Database migrations run with `supabase db push` against the production project.
- Health checks gate the rollout. A failing `/api/health` aborts and rolls back.

## 6. Required secrets in production

- `ANTHROPIC_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `SESSION_SECRET`
- `SENTRY_DSN` (recommended)

Rotation cadence target: 90 days. Document each rotation in `docs/DECISIONS.md` as an entry.

## 7. Observability

- **Logs**: structured JSON, shipped to whichever sink staging/prod uses (TBD).
- **Errors**: Sentry, separate projects per environment.
- **Traces**: OTLP exporter; sampling 100% in staging, 10% in prod (target).
- **Metrics to watch**: parser error rate, Places quota burn, Pytrends backlog age, LLM verifier flag rate.

## 8. Backups

- Supabase managed Postgres backups daily, 7 day retention (default plan; revisit at scale).
- Uploaded files: rely on Supabase Storage versioning + lifecycle policy.
- Application state outside the DB is stateless; containers can be destroyed at will.

## 9. Disaster recovery (target)

- RPO ≤ 24 h (daily DB backup).
- RTO ≤ 4 h to rebuild from compose + secrets + Supabase restore.

## 10. CI / CD (target — Phase 8)

- Lint (ruff for Python, eslint+prettier for TS) on every PR.
- Type checks (mypy, tsc) on every PR.
- Unit + integration tests on every PR.
- Build images on tag.
- Deploy to staging on merge to `main`; production via manual workflow.

## 11. What is NOT deployed

- No local Postgres in production compose — Supabase handles it.
- No Pytrends in the synchronous request path — scheduler-only.
- No raw client CSVs in any container image — uploads go straight to Supabase Storage.
