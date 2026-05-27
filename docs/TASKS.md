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

**Entry criteria:** Phase 0 exit. Python version decided (3.13). Package manager: bootstrapped with `pip + venv`; migration to `uv` (ADR-0009) is a Phase 2 entry criterion.

**Deliverables**
- [x] `backend/` Python project (`pyproject.toml`, ruff, mypy — all configured; ruff and mypy both pass clean on `app/`)
- [x] FastAPI app skeleton with `/api/health`
- [x] Parser resolving `BD 2026` sheet (xlsx + csv) — CSV fully supported; Excel reads by sheet name, never by index; multi-sheet round-trip test asserts `BD 2026` is picked even when it's not first
- [x] Typed `DataParserError` hierarchy — `MissingSheetError`, `MissingColumnError`, `MoneyParseError`, `RatioOutOfRangeError`, `EncodingError`, `UnsupportedFormatError`
- [x] Cleaning rules — asterisk, period, money (strict; raises on bad values), ratio (validated to `[0, 1.5]`), accent (NFC on headers and cells), drop `TOTAL == 0`
- [x] Synthetic fixtures under `backend/tests/fixtures/` (renamed from `data/sample/` per the Phase 1 prompt — no real client data)
- [x] Unit tests covering all parser error classes

**Exit criteria**
- [x] Parser handles a synthetic multi-sheet workbook correctly (`test_excel_resolves_bd_2026_not_first_sheet`, `test_excel_missing_bd_2026_raises_missing_sheet`)
- [x] 100% of typed errors have a test
- [x] `POST /api/upload` returns `202` with `sheet_resolved` and `warnings`

**Phase 1 status:** complete. 20/20 tests green, ruff clean, mypy clean on `app/`.

**Phase 1.x carryover (handled at Phase 2 entry):**
- Migrate the backend from `pip + venv` to `uv` per ADR-0009 — generate `uv.lock`, switch canonical commands to `uv sync` / `uv run pytest`.
- Pin transitive dependencies via the lockfile (the only Phase 1 bug came from `pandas` jumping to 3.0 under an unpinned `>=2.2` spec).
- Case-insensitive header matching (currently only whitespace + NFC); needed once real client workbooks vary in capitalization.

---

## Phase 2 — Deterministic analytics

**Entry criteria:** Phase 1 exit. ADR-0008 through ADR-0013 accepted (see [DECISIONS.md](DECISIONS.md)). Backend migrated to `uv` (uv.lock committed; `uv sync` and `uv run pytest` are the canonical commands).

**Scope rule.** All analytics are **deterministic Python**. No LLM, no Places, no Pytrends, no persistence, no frontend. Pure functions on cleaned DataFrames.

**Deliverables**

*Data scoping & coverage metadata*
- [ ] Thread `dataset_scope` from the parser output (Phase 1 `ParseResult`) into every analytics input and output. Default scope `nama_2026`; the 2025 reference CSV is `reference_2025` and is opted into explicitly. (ADR-0012)
- [ ] Implement **period coverage validation**: every analytics result carries `period_coverage = { declared: [...], actual: [...], missing: [...] }`. The declared window for the current study is `ENERO 2026 … ABRIL 2026`; actual is whatever the data contains. (ADR-0013)
- [ ] Emit a **missing-month warning** when `missing` is non-empty. The warning text is Spanish-ready (English internal code, Spanish surface copy via i18n in Phase 6). Propagate the warning through the analytics return value so downstream (UI, report, LLM prompt) all see it.
- [ ] Reference-data **contamination guard**: a single function (`assert_nama_only(df)` or similar) that every NAMA analytics function calls. It raises a typed error if `dataset_scope != "nama_2026"` rows are present. Test that the guard fires on a mixed fixture.
- [ ] Update [PRODUCT_SPEC.md](PRODUCT_SPEC.md) to reframe the current study as Q1 2026 (enero–marzo) until April arrives. (ADR-0013)

*Analytics modules (all deterministic)*
- [ ] `analytics/margins.py` — utilidad bruta, margen bruto, cost leakage. Recomputed values compared to source values within tolerance.
- [ ] `analytics/menu_engineering.py` — estrellas / caballos de batalla / puzzles / perros. Median computed per `(sucursal, period)`; strict `>=` on the volume axis.
- [ ] `analytics/alerts.py` — five alert rules from [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 4, with severities and Spanish-ready message templates.
- [ ] `analytics/sensitivity.py` — 5% input-cost shock.
- [ ] `analytics/coverage.py` — period coverage + missing-month logic; consumed by every metric module.
- [ ] All analytics modules expose **pure** `(DataFrame, params) → result` signatures. No I/O, no DB, no API calls.

*Tests*
- [ ] Golden-number tests for every metric.
- [ ] Boundary tests on menu engineering quadrants (at-median cases).
- [ ] Below / at / above tests on every alert threshold.
- [ ] Period-coverage tests: declared = 4 months, actual = 3 months → missing warning present, value is `["ABRIL 2026"]`.
- [ ] Contamination-guard tests: mixed-scope fixture raises; pure NAMA fixture passes.
- [ ] Sensitivity tests: cost × 1.05 produces the expected new margin.

*Documentation*
- [ ] Update [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 6 to include `dataset_scope` and `period_coverage` on the deterministic JSON contract handed to the LLM in Phase 5.

**Exit criteria**
- Recomputed margins match source-provided margins within tolerance on the NAMA sample.
- All alerts trigger correctly on synthetic edge cases.
- Every analytics output includes `dataset_scope` and `period_coverage`.
- Mixing `nama_2026` and `reference_2025` rows in a NAMA analysis run **always** raises (no silent contamination).
- The Q1 framing is reflected in [PRODUCT_SPEC.md](PRODUCT_SPEC.md) and the missing-month warning is exercised by tests.

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
