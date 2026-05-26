# Architecture

## 1. The four-layer rule

```
Python calculates.     ← Pandas, NumPy. Pure functions. The single source of truth for numbers.
Supabase persists.     ← Postgres + Auth + Storage. Every metric ends up in a row.
Google Places contextualizes.  ← Competitor density, ratings, reviews, review velocity, sentiment.
Claude interprets.     ← Reads precomputed JSON. Produces Spanish prose. Never arithmetic.
```

No layer skips its predecessor. The LLM never reads raw CSV rows. The frontend never computes a financial number client-side.

## 2. Runtime topology

```
┌──────────────┐    ┌────────────┐    ┌─────────────────────┐
│  Next.js UI  │◄──►│  FastAPI   │◄──►│   Supabase / PG     │
│ (Spanish)    │    │  (Python)  │    │ clients, periods,   │
└──────────────┘    └─────┬──────┘    │ runs, memory, ...   │
                          │           └─────────────────────┘
                          │
                   ┌──────┴───────┐
                   │   Workers    │  ← background queue (Redis-backed)
                   │  ┌────────┐  │
                   │  │Places  │  │  ← sync-on-demand + scheduled refresh
                   │  ├────────┤  │
                   │  │Pytrends│  │  ← async ONLY; cron
                   │  ├────────┤  │
                   │  │ Claude │  │  ← interpretation runs
                   │  └────────┘  │
                   └──────────────┘
```

- **api** — synchronous HTTP. Parses uploads, runs deterministic analytics, reads/writes Supabase, enqueues background jobs. **Never** blocks on Pytrends.
- **worker** — pulls jobs from Redis: Places enrichments, Pytrends snapshots, LLM interpretation.
- **scheduler** — periodic refreshers (Places TTL, Pytrends cron).
- **web** — Next.js, server components allowed; no client-side financial math.

## 3. Module map (target — Phase 1+)

```
backend/rga/
  parser/        ← Excel/CSV → typed DataFrames. Resolves `BD 2026` sheet.
  analytics/     ← deterministic metric functions; pure; unit-tested with golden numbers.
    margins.py
    menu_engineering.py
    alerts.py
    sensitivity.py
  persist/       ← Supabase repositories. One module per table cluster.
  enrich/
    places/      ← Google Places client, search, reviews, sentiment.
    pytrends/    ← async worker only; cached snapshots.
  llm/
    prompt.py    ← 5-block builder.
    compress.py  ← Haiku compression of memory >6k tokens.
    interpret.py ← orchestrator.
  api/           ← FastAPI routes (see API_SPEC.md).
  jobs/          ← worker + scheduler entrypoints.
  schemas/       ← Pydantic models, including the deterministic JSON
                   contract passed to Claude.

frontend/web/
  app/           ← Next.js App Router; Spanish copy only.
  components/
    cards/       ← atomic insight cards (one insight each).
    semaphore/   ← financial semaphore (green/amber/red) primitives.
  lib/api/       ← typed API client.
```

## 4. Data flow for an upload

1. User uploads `.xlsx` / `.csv` to `POST /api/upload`.
2. Parser resolves the `BD 2026` sheet by name. If missing → `DataParserError`.
3. Cleaning rules apply (see DATA_CONTRACTS.md). Malformed rows fail loudly.
4. Cleaned DataFrame → analytics layer → metrics dict.
5. Metrics persisted to Supabase: `financial_periods`, `analysis_runs`, `llm_insights` (later).
6. Enrichment jobs enqueued for each `(client_id, sucursal)`.
7. Front-end polls / subscribes; once the run is ready, dashboard re-renders.

## 5. Database tables (target)

Defined in `docs/DATA_CONTRACTS.md` § "Persistence schema". Core list:

- `clients`
- `client_memory`
- `uploaded_files`
- `financial_periods`
- `analysis_runs`
- `chat_messages`
- `external_signals`
- `places_searches`
- `places`
- `competitors`
- `place_reviews`
- `llm_insights`
- `reports`

## 6. Cross-cutting concerns

- **Determinism.** All analytics functions are pure: `(DataFrame, params) → metrics`. Tested against golden fixtures.
- **Time zone.** `America/Mexico_City` everywhere user-facing. Storage is UTC.
- **Idempotency.** Re-uploading the same workbook produces the same metric rows (deduped by file hash).
- **Failure isolation.** Places / Pytrends errors are logged + surfaced as "signals not available", but never abort the run.
- **Spanish boundary.** The boundary where text becomes Spanish is the LLM prompt + UI catalog. Code, logs, error messages → English.

## 7. What changes per phase

| Phase | New modules | New tables |
|---|---|---|
| 1 | `parser/`, `api/` skeleton | — |
| 2 | `analytics/*`, `schemas/` | — |
| 3 | `persist/*` | all DDL |
| 4 | `enrich/places/` | `places_*`, `competitors`, `place_reviews` |
| 5 | `llm/*` | `llm_insights`, `client_memory` |
| 6 | `frontend/*` | — |
| 7 | `reports/` | `reports` |
| 8 | Dockerfiles, CI | — |
| 9 | hardening, RLS, observability | RLS policies |
