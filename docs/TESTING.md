# Testing

## 1. What "tested" means here

For this product, "tested" specifically means **the numbers are right**. Coverage percentages are secondary. The financial analytics layer is the highest priority.

## 2. Test pyramid

```
                ┌──────────────────────┐
                │  Golden-number tests │   ← THE most important layer
                └──────────────────────┘
              ┌──────────────────────────┐
              │   Unit tests (analytics, │
              │   parser, prompt builder)│
              └──────────────────────────┘
            ┌──────────────────────────────┐
            │   Integration (API + DB)     │
            └──────────────────────────────┘
          ┌──────────────────────────────────┐
          │   E2E (happy-path upload + chat) │
          └──────────────────────────────────┘
```

## 3. Golden-number tests

- Live under `backend/tests/golden/`.
- Use small anonymized fixtures committed under `data/sample/`.
- For each canonical metric in [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 2, assert exact equality to a hand-computed expected value.
- Recomputed `UTILIDAD BRUTA` / `MARGEN BRUTO` are validated against both the source-provided figure and the analytics result.

## 4. Parser tests

- One test per `DataParserError` subclass — fixture deliberately broken in that one way.
- `BD 2026` sheet resolution: tests for present-at-index-0, present-at-index-3, absent, name-with-trailing-space, lowercase variant.
- Money parsing: `"$1,234.56"`, `"-$1,234.56"`, `""`, `"$0.76"` (the MARGEN BRUTO ratio gotcha), `"abc"` (must raise).
- Cleaning rules: leading `*`, trailing `.`, accent normalization round-trips.

## 5. Analytics tests

- Pure-function tests with synthetic DataFrames.
- Menu engineering quadrants: tests at the median boundaries (`>=` strict).
- Alerts: each threshold has a "just below", "at threshold", "just above" case.
- Sensitivity: `costs * 1.05` produces the expected new margin.

## 6. Persistence tests

- Run against a local Supabase or `pgtap`-style isolated test schema.
- Idempotency: same file hash → same row counts.
- RLS: a non-owner cannot read another client's metrics.

## 7. Enrichment tests

- **No live Google Places calls in CI.** Use recorded fixtures (vcr-style) or mock the client.
- Backoff: simulate 429 and assert retry timing.
- Failure isolation: when Places raises, `/api/clients/{id}/metrics` still returns financials.

## 8. LLM tests

- The prompt builder is tested deterministically: given inputs X, the assembled prompt is exactly Y.
- The numeric verifier is unit-tested with synthetic outputs (number present in JSON → pass; number absent → flag).
- LLM calls themselves are not in CI by default; an opt-in nightly job runs against a small "smoke" prompt set with a fixed seed and asserts the verifier passes.

## 9. UI tests

- Component tests for cards, semaphore, chat surface.
- Visual regression on the dashboard page in Spanish (rule: any English string in the snapshot fails the test).
- Accessibility checks: axe-core on every page.

## 10. CI matrix (target)

- Python: 3.12 (single version for v1).
- Node: 20 LTS.
- OS: Linux for CI; macOS dev only.
- Migrations run before integration tests in CI.

## 11. Local commands (target — exist Phase 1+)

```
make test            # all backend tests
make test-golden     # only the golden-number tests
make test-fast       # skip integration + e2e
make lint
make typecheck
```

None of these exist yet — Phase 0 has no tooling.

## 12. Test data discipline

- **Never** commit NAMA data to test fixtures.
- Test fixtures live in `data/sample/` and are explicitly anonymized.
- Synthetic fixtures preferred over reductions of real data.
