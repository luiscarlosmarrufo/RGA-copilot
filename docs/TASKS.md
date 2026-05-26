# Tasks

Phased task tracker. Each phase has **entry criteria**, **deliverables**, and **exit criteria**. Do not open a phase until the previous phase's exit criteria are signed off in [DECISIONS.md](DECISIONS.md).

Status legend: ` ` todo · `~` in progress · `x` done · `-` cut/deferred.

---

## Phase 0 — Repository operating system

**Entry criteria:** repo initialized.

**Deliverables**

- [x] `README.md` (top-level overview, phases)
- [x] `CLAUDE.md` (operating instructions for Claude Code)
- [x] `.env.example`
- [x] `docker-compose.yml`, `docker-compose.dev.yml` (placeholders)
- [x] `docs/PRODUCT_SPEC.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/DATA_CONTRACTS.md`
- [x] `docs/API_SPEC.md`
- [x] `docs/UI_SPEC.md`
- [x] `docs/GOOGLE_PLACES_STRATEGY.md`
- [x] `docs/ANTI_HALLUCINATION.md`
- [x] `docs/DEPLOYMENT.md`
- [x] `docs/TESTING.md`
- [x] `docs/DECISIONS.md`
- [x] `docs/TASKS.md` (this file)
- [x] `.claude/rules/*.md`
- [x] `.claude/skills/*/SKILL.md`
- [x] `.claude/agents/*.md`

**Exit criteria**
- All docs reviewed by the architect agent / user.
- Open ADRs (web hosting, package manager, queue, report format, 2025 CSV location, Abril 2026 gap) are resolved or explicitly deferred.
- `.gitignore` cleaned (remove the literal heredoc lines).

---

## Phase 1 — Backend skeleton + parser

**Entry criteria:** Phase 0 exit. Package manager + Python version decided.

**Deliverables**
- [ ] `backend/` Python project (pyproject.toml, ruff, mypy)
- [ ] FastAPI app skeleton with `/api/health`
- [ ] `rga/parser/` resolving `BD 2026` sheet (xlsx + csv)
- [ ] Typed `DataParserError` hierarchy
- [ ] Cleaning rules (asterisk, period, money, ratio, accent, drop TOTAL==0)
- [ ] Golden fixtures in `data/sample/`
- [ ] Unit tests covering all parser error classes

**Exit criteria**
- Parser handles a synthetic multi-sheet workbook correctly.
- 100% of typed errors have a test.
- `POST /api/upload` returns `202` with `sheet_resolved` and warnings.

---

## Phase 2 — Deterministic analytics

**Entry criteria:** Phase 1 exit.

**Deliverables**
- [ ] `analytics/margins.py` (utilidad bruta, margen bruto, cost leakage)
- [ ] `analytics/menu_engineering.py` (estrellas / caballos / puzzles / perros)
- [ ] `analytics/alerts.py` (5 alert rules with severities)
- [ ] `analytics/sensitivity.py` (5% cost shock)
- [ ] Golden-number tests for every metric

**Exit criteria**
- Recomputed margins match source-provided margins within tolerance for NAMA sample.
- All alerts trigger correctly on synthetic edge cases.

---

## Phase 3 — Supabase persistence

**Entry criteria:** Phase 2 exit. Supabase projects created (dev/staging/prod).

**Deliverables**
- [ ] Migrations for: `clients`, `client_memory`, `uploaded_files`, `financial_periods`, `analysis_runs`, `chat_messages`, `external_signals`, `llm_insights`, `reports`
- [ ] `rga/persist/` repositories
- [ ] Idempotent re-upload by file hash

**Exit criteria**
- Round-trip a parse+analytics run from API to DB and back.
- RLS skeleton in place (full audit in Phase 9).

---

## Phase 4 — Google Places intelligence

**Entry criteria:** Phase 3 exit. Google Maps API key provisioned.

**Deliverables**
- [ ] `enrich/places/` client with backoff and quota guard
- [ ] Migrations: `places_searches`, `places`, `competitors`, `place_reviews`
- [ ] `analytics/market.py` (competitive index, sentiment, review velocity)
- [ ] Scheduler job: nightly refresh
- [ ] `POST /api/signals/refresh` (places synchronous if warm cache)
- [ ] Failure isolation tests

**Exit criteria**
- A Places outage does not affect `/api/clients/{id}/metrics`.
- All Places derived metrics computed in Python, never asked of Claude.

---

## Phase 5 — LLM prompt builder

**Entry criteria:** Phase 4 exit.

**Deliverables**
- [ ] `llm/prompt.py` with the 5 immutable blocks
- [ ] `llm/compress.py` (Haiku) for memory > `LLM_MEMORY_TOKEN_BUDGET`
- [ ] `llm/verify.py` numeric verifier
- [ ] `POST /api/chat` (streaming SSE with routing chips)
- [ ] `POST /api/memory/compress`

**Exit criteria**
- Verifier blocks responses with uncited numbers in test cases.
- Routing chips never leak chain-of-thought.

---

## Phase 6 — Frontend dashboard

**Entry criteria:** Phase 5 exit. Web hosting ADR resolved.

**Deliverables**
- [ ] Next.js scaffold in `frontend/`
- [ ] Spanish i18n catalog as the only source of UI strings
- [ ] Fixed sidebar (Dashboard, Reportes, Documentos, Tareas, Roadmap, Perfil)
- [ ] Atomic insight cards + premium semaphore
- [ ] Chat surface with optimistic UI + routing chips
- [ ] Citation chips on every number

**Exit criteria**
- A consultor can load NAMA's run and read the executive summary in Spanish end-to-end.
- Lint forbids English strings in i18n catalogs.

---

## Phase 7 — Reports

**Entry criteria:** Phase 6 exit. Report format ADR resolved.

**Deliverables**
- [ ] Spanish report template (executive summary, sucursal pages, market section)
- [ ] PDF + Markdown export
- [ ] `GET /api/clients/{id}/reports`
- [ ] Storage to Supabase Storage with signed URLs

**Exit criteria**
- Report numbers match dashboard numbers exactly.
- Typography passes accent / character-set review.

---

## Phase 8 — Docker / deploy readiness

**Entry criteria:** Phase 7 exit.

**Deliverables**
- [ ] `backend/Dockerfile` (multi-stage, dev + prod targets)
- [ ] `frontend/Dockerfile`
- [ ] CI pipeline: lint, typecheck, tests, build, push image
- [ ] Staging deploy automation
- [ ] Production deploy via tag

**Exit criteria**
- `docker compose up` builds and serves the app from scratch.
- Staging mirrors production topology.

---

## Phase 9 — Hardening

**Entry criteria:** Phase 8 exit.

**Deliverables**
- [ ] Rate limits per [API_SPEC.md](API_SPEC.md) § "Rate limits"
- [ ] Full RLS audit
- [ ] Observability: Sentry, OTLP traces, parser/Places/LLM metrics
- [ ] Numeric verifier upgraded from "flag" to "block + regenerate"
- [ ] Secret rotation procedure documented and exercised
- [ ] Backup / restore drill

**Exit criteria**
- Production incident response runbook signed off.
- Numeric verifier flag rate < 1% on the smoke prompt set.
