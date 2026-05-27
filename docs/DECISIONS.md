# Architectural Decisions (ADR log)

Append-only. Each decision is dated and numbered. Do not edit past entries — supersede with a new ADR.

Format:
```
## ADR-NNNN — Title
Date: YYYY-MM-DD
Status: proposed | accepted | superseded by ADR-XXXX
Context:
Decision:
Consequences:
```

---

## ADR-0001 — Four-layer architecture
Date: 2026-05-26
Status: accepted

**Context.** We need clear ownership of each capability so that LLM hallucination cannot contaminate financial numbers and so that external API failures cannot break the core product.

**Decision.** Adopt a strict four-layer separation:

```
Python calculates.  Supabase persists.  Google Places contextualizes.  Claude interprets.
```

**Consequences.**
- All financial math lives in Pandas; LLMs receive precomputed JSON.
- Places/Pytrends outages degrade signals but never break analytics.
- Frontend never computes financial numbers client-side.

---

## ADR-0002 — `BD 2026` is the canonical sheet name
Date: 2026-05-26
Status: accepted

**Context.** Source Excel workbooks contain many sheets. Picking the first one is unsafe.

**Decision.** The parser resolves the transactional sheet by **name** = `BD 2026` (case-insensitive, trimmed). Absent sheet → `MissingSheetError`. CSV uploads are treated as that single sheet.

**Consequences.** The parser is robust to sheet reordering. Callers must label new workbooks accordingly. Future studies may bump the year suffix; resolution will need a configurable pattern.

---

## ADR-0003 — Pytrends is async-only
Date: 2026-05-26
Status: accepted

**Context.** Pytrends is unofficial, rate-limited, and prone to 429s. Putting it in the request path will hang the UI.

**Decision.** Pytrends only runs in scheduled/background jobs. The UI reads the cached snapshot. `/api/signals/refresh` for pytrends always returns `202`.

**Consequences.** Trends data may lag by up to one cron cycle. The product MVP does not block on trends availability.

---

## ADR-0004 — Supabase as managed Postgres
Date: 2026-05-26
Status: accepted

**Context.** We need Postgres, Auth, Storage, and RLS without operating a database.

**Decision.** Use Supabase for the production database. Do not run a `postgres` container in compose.

**Consequences.** Lock-in to Supabase SDK and migration workflow. Local dev uses the real Supabase project (a dedicated dev project) rather than a local Postgres.

---

## ADR-0005 — Claude never performs arithmetic
Date: 2026-05-26
Status: accepted

**Context.** LLMs are unreliable at arithmetic, and even when correct they cannot be audited.

**Decision.** Claude responses must cite numbers verbatim from the deterministic JSON. A post-response verifier extracts numeric tokens and matches them against the JSON. See [ANTI_HALLUCINATION.md](ANTI_HALLUCINATION.md).

**Consequences.** Some user questions ("¿cuál sería el margen si subimos precio 5%?") must be routed back to the analytics layer first, then re-prompted with the new JSON.

---

## ADR-0006 — Spanish at the user boundary
Date: 2026-05-26
Status: accepted

**Context.** Audience is Mexican consultants and business owners. Mixed-language UIs erode trust.

**Decision.** UI, alerts, report prose, chat replies → Spanish (`es-MX`). Code, comments, commit messages, engineering docs → English. The language boundary is the LLM system prompt and the UI i18n catalog.

**Consequences.** A single change of audience (e.g. English-speaking client) requires a deliberate i18n project, not a flag flip.

---

## ADR-0007 — Phased delivery (0 → 9)
Date: 2026-05-26
Status: accepted

**Context.** Building everything in parallel will produce inconsistencies between layers and unauditable numbers.

**Decision.** Strict phased delivery as listed in [TASKS.md](TASKS.md). A phase opens only after the previous phase's exit criteria are signed off here.

**Consequences.** Slower perceived progress in early phases; predictable correctness later.

---

## ADR-0008 — Web framework hosting: Docker Compose now, Vercel optional later
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (Web framework hosting)

**Context.** The frontend will be Next.js. Two viable paths: deploy to Vercel (edge runtime, Vercel-specific features) or run inside `docker-compose.yml` alongside the API.

**Decision.** Use Docker Compose for local development and the MVP. The Next.js app runs as a service in `docker-compose.yml` like the rest of the stack. Vercel remains an option for a later production deployment, but **do not optimize for Vercel-only behavior** in the meantime — no Vercel Edge runtimes, no `@vercel/*` SDKs, no Image Optimization that requires Vercel's CDN.

**Consequences.**
- Single deploy topology in MVP: one compose file boots everything.
- Frontend ships as a standard Node/Next.js Docker image (Phase 8 deliverable).
- Migrating to Vercel later requires a deliberate review pass — no accidental coupling expected, because Vercel-specific APIs are forbidden.
- Edge-perf optimizations are deferred; we'll likely accept slightly higher TTFB for the MVP.

---

## ADR-0009 — Python package manager: uv
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (Package manager)

**Context.** Phase 1 was bootstrapped with `pip + venv` because `uv` was not installed locally. Going forward we need a single, reproducible, fast package manager for the backend.

**Decision.** **Use `uv`** for the backend. The backend must:

- Keep `backend/pyproject.toml` as the source of truth for dependencies.
- Add and commit `backend/uv.lock` (generated by `uv lock`).
- Use `uv sync` for environment setup (creates and manages `.venv`).
- Use `uv run <cmd>` (e.g. `uv run pytest`, `uv run uvicorn …`) for all backend commands going forward.
- Do **not** use Poetry. Do not maintain a `requirements.txt` alongside the lockfile.

`uv` is fast (Rust-implemented), deterministic via lockfile, and resolves the version-drift problem we already hit (Phase 1 pulled `pandas` 3.0 under a `>=2.2` spec; the lockfile pins exact versions).

**Consequences.**
- Anyone working on the backend needs `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`).
- CI installs `uv`, then `uv sync`, then `uv run pytest`. No editable-install fiddling.
- Docker images use the official `ghcr.io/astral-sh/uv` base or install `uv` in a build stage; final image still ships only Python + pinned deps.
- Migration cost from the current `pip` setup: minimal — just run `uv lock` once and update the Makefile / docs.
- All Phase 1 instructions in [docs/DEPLOYMENT.md](DEPLOYMENT.md) and Makefile placeholders need a follow-up edit before Phase 2 starts. Tracked as a Phase 2 entry-criterion item in [TASKS.md](TASKS.md).

---

## ADR-0010 — Job queue deferred; RQ + Redis when needed
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (Job queue)

**Context.** Phases 4 (Places enrichment), 5 (LLM interpretation, memory compression), and the scheduled Pytrends pipeline all need background work. The compose file already declares `worker` and `scheduler` services. The choice has been between RQ, Arq, and Celery.

**Decision.** **Do not implement a queue in Phase 2.** Phase 2 is deterministic analytics on already-loaded data; it does not require background jobs. Defer the queue until the first feature actually needs it (currently expected in Phase 4).

When the queue is introduced, use **RQ with Redis** unless a concrete requirement justifies switching to Arq (native asyncio) or Celery (multi-broker, beats, complex routing). RQ is the simplest choice for the workloads we anticipate (Places refresh, Pytrends snapshot, LLM call): synchronous-feeling Python functions enqueued by HTTP handlers, executed by worker processes against a Redis broker.

**Consequences.**
- Phase 2 ships without `worker` / `scheduler` containers actually running anything. The compose entries remain as placeholders; their `command:` lines stay un-implemented until Phase 4 starts.
- The `REDIS_URL` env var in `.env.example` is dormant until Phase 4.
- Switching to Arq or Celery later is feasible but costly — we capture that here so the next ADR can be written with eyes open. Concrete triggers that would justify revisiting:
  - Need for periodic schedules (Celery Beat) that RQ-Scheduler can't cover.
  - Native asyncio worker required because an integration only ships an async client (Arq).
  - Multi-tenant routing across many queues / brokers (Celery).

---

## ADR-0011 — Report format: structured `report_json` first; PDF engine deferred
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (Report format)

**Context.** Phase 7 generates Spanish reports for RGA consultants. Candidate PDF engines: Typst, ReportLab, HTML→Chromium/Playwright. Each has trade-offs around Spanish typography, fidelity to the web dashboard, and operational complexity.

**Decision.** Do **not** select a PDF engine yet. Phase 7 generates a structured **`report_json`** first — a deterministic, versioned document tree with all sections, numbers, and citations. The rendered PDF is a separate concern downstream.

When the PDF engine is selected (likely during Phase 7), the leading candidate is **HTML→Chromium/Playwright**, because the report should visually match the web dashboard (same components, same palette, same typography). **Typst** remains an alternative if Spanish typography or formal PDF layout becomes the dominant requirement and the HTML route can't meet it.

**Consequences.**
- `report_json` is the contract; the engine is an implementation detail under it.
- Frontend and report renderer share Spanish copy, palette, and number formatting — no drift between dashboard and report.
- Playwright in the production image adds significant weight (Chromium binary). Acceptable given the fidelity payoff; revisit if image size becomes a deploy blocker.
- A second engine could be added without changing the persisted reports — we'd re-render the same `report_json`.

---

## ADR-0012 — Non-NAMA 2025 CSV is quarantined reference data
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (2025 reference CSV location)

**Context.** `data/private/SG - Cliente 2025 - BD 2025.csv` is from a different client (Amazon B2C marketplaces), not Grupo NAMA. It sits next to NAMA data today and risks being aggregated by accident — a confidentiality and data-quality hazard.

**Decision.** Treat the 2025 file as **quarantined reference-only data**.

- It must **not** be included in default NAMA analysis runs.
- The parser and analytics pipeline must carry a `dataset_scope` metadata field on every record / result set (e.g. `nama_2026`, `reference_2025`, …).
- Default scope for any NAMA run is `nama_2026`. Reference data is opted into explicitly with a separate scope, never mixed.
- Tests must assert that NAMA analysis runs cannot pick up rows whose `dataset_scope != "nama_2026"`. The test fails loudly on cross-contamination.

Physical relocation of the file (e.g. moving it under `data/private/reference/`) is a follow-up, not the decision itself; the load-bearing change is the `dataset_scope` propagation.

**Consequences.**
- Phase 2 must thread `dataset_scope` through the parser output, the analytics inputs, and any persisted artifact (when Phase 3 lands).
- Phase 3 schema adds a `dataset_scope` column to relevant tables; cross-scope joins are explicitly forbidden in the data access layer.
- Anonymized fixtures in `data/sample/` similarly carry a scope, making it impossible to write a test that accidentally aggregates across scopes.

---

## ADR-0013 — Abril 2026 data gap: narrow study to Q1 2026; emit period-coverage warnings
Date: 2026-05-26
Status: accepted
Supersedes: ADR-TBD (Abril 2026 data gap)

**Context.** The 2026 NAMA workbook contains data for ENERO, FEBRERO and MARZO 2026 only. The declared study window is enero–abril 2026. We have to choose between (a) waiting on Abril before producing any analysis, (b) imputing Abril, (c) formally narrowing the current study to Q1.

**Decision.** **Do not impute.** Formally narrow the current study to **Q1 2026 (ENERO–MARZO 2026)** until Abril data is obtained from the client. When Abril arrives, widen the window by re-running analyses against the updated workbook.

To make this safe and visible:

- Phase 2 analytics must compute and surface a **`period_coverage`** metadata field on every result set, containing the list of months actually present (e.g. `["ENERO 2026", "FEBRERO 2026", "MARZO 2026"]`) plus the declared study window.
- Analytics must emit a **missing-period warning** when the declared window is wider than the data covers. The warning is propagated to the UI, the report, and the LLM prompt context (so Claude does not infer over months we don't have).
- No analytics function silently "extrapolates" from Q1 to a year or to abril. Any forward-looking statement is gated on actual data being present.

**Consequences.**
- The MVP report says Q1 2026 explicitly. No mention of April unless April rows exist.
- Adding April later requires no code change — re-running over the updated CSV widens `period_coverage` automatically.
- The user-facing copy in [docs/PRODUCT_SPEC.md](PRODUCT_SPEC.md) should reflect the Q1 framing; that follow-up edit is tracked in [TASKS.md](TASKS.md) as part of Phase 2.

---

## Open decisions (not yet resolved)

*(All Phase-0-era ADRs are now resolved. New open items will be added here as they arise.)*
