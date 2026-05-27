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
- [x] Thread `dataset_scope` from the parser output (Phase 1 `ParseResult`) into every analytics input and output. Default scope `nama_2026`; the 2025 reference CSV is `reference_2025` and is opted into explicitly. Parser stamps a `dataset_scope` column on the cleaned DataFrame; ParseResult carries it as a field. (ADR-0012)
- [x] Implement **period coverage validation** in `analytics/coverage.py` — `compute_period_coverage` returns `{declared, actual, missing, unexpected}`. (ADR-0013)
- [x] Emit a **missing-month warning** via `missing_period_warning(coverage)` with payload `{code: "missing_periods", missing, declared, actual}`. Shape matches the LLM contract in [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 6.
- [x] Reference-data **contamination guard** in `analytics/scope.py` (`assert_nama_only(df)`). Every NAMA analytics function calls it; mixed-scope frame raises `DatasetScopeError`. (ADR-0012)
- [x] Update [PRODUCT_SPEC.md](PRODUCT_SPEC.md) to reframe the current study as Q1 2026 until April arrives.

*Analytics modules (all deterministic)*
- [x] `analytics/margins.py` — `utilidad_bruta`, `margen_bruto`, `cost_leakage`, `cost_leakage_ratio`, `aggregate_margins_per_sucursal`. Recomputed values compared to source values within tolerance.
- [x] `analytics/menu_engineering.py` — estrellas / caballos de batalla / puzzles / perros. Median computed per `(sucursal, period)` via `groupby.transform("median")`; strict `>=` on both axes.
- [x] `analytics/alerts.py` — three deterministic financial alerts: `low_margin`, `profit_concentration` (MEDIUM / HIGH at 40% / 50%), `inefficient_line`. Maps and Trends alerts are intentionally deferred to Phase 4.
- [x] `analytics/sensitivity.py` — `shock_costs(df, factor=1.05)` with recomputed `UTILIDAD BRUTA` and `MARGEN BRUTO`; input never mutated.
- [x] `analytics/coverage.py` — period coverage + missing-month logic.
- [x] All analytics modules expose **pure** `(DataFrame, params) → result` signatures. No I/O, no DB, no API calls.

*Tests*
- [x] Golden-number tests for every metric (`test_analytics_margins.py`, `test_analytics_sensitivity.py`).
- [x] Boundary tests on menu engineering quadrants (at-median ties land on the HIGH side; `test_analytics_menu_engineering.py`).
- [x] Strict-boundary tests on alert thresholds — both `low_margin` at exactly −5 pp and `inefficient_line` at exactly −2 pp do **not** fire, with float-precision guard (`_strictly_below_pp` rounds delta to 6 decimal pp).
- [x] Period-coverage tests: declared = 4 months, actual = 3 months → missing warning surfaces `["ABRIL 2026"]`.
- [x] Contamination-guard tests: mixed-scope fixture raises; pure NAMA fixture passes.
- [x] Sensitivity tests: cost × 1.05 produces the expected new margin; negative factor rejected.

*Documentation*
- [x] Update [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 6 to include `dataset_scope` and `period_coverage` on the deterministic JSON contract handed to the LLM in Phase 5.

**Exit criteria**
- [x] Recomputed margins match source-provided margins exactly on the analytics sample (12 rows × 3 sucursales).
- [x] All Phase 2 alerts trigger correctly on synthetic edge cases (strict-boundary tests + cleaned-fixture tests).
- [x] Every analytics output includes `dataset_scope` (column on the DataFrame; field on ParseResult). `period_coverage` is computed on demand via `compute_period_coverage`; warning shape is finalized.
- [x] Mixing `nama_2026` and `reference_2025` rows in a NAMA analysis run **always** raises (verified by `test_analytics_scope.py` and `test_scope_guard_blocks_reference_rows_in_margins`).
- [x] Q1 framing reflected in [PRODUCT_SPEC.md](PRODUCT_SPEC.md); missing-month warning exercised by tests.

**Phase 2 status:** complete. 58/58 tests green, ruff clean, mypy clean on 20 source files. Backend now runs under `uv` (`uv.lock` committed; canonical commands `uv sync`, `uv run pytest`, `uv run ruff check app tests`, `uv run mypy app`).

**Carryover into Phase 3:**
- The `period_coverage` payload is produced on demand by analytics callers; Phase 3 should persist it alongside `analysis_runs` so the UI and LLM prompt always see the same coverage snapshot.
- Pandas 3.0 quirks bit Phase 1 (string dtype) and Phase 2 (`include_groups` removed from `groupby.apply`). Pin the major in pyproject when adding new dependencies; revisit if pandas 3.1 lands.

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
