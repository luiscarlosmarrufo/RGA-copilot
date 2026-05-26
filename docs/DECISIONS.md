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

## Open decisions (not yet resolved)

- **ADR-TBD — Web framework hosting**: Next.js on Vercel vs in-compose. Trade-off: edge perf vs single-deploy simplicity.
- **ADR-TBD — Package manager**: `uv` vs Poetry for the Python backend.
- **ADR-TBD — Job queue**: RQ vs Arq vs Celery. Leaning RQ for simplicity.
- **ADR-TBD — Report format**: PDF via Typst, ReportLab, or HTML→Chromium. Spanish typography quality matters.
- **ADR-TBD — Where to store the non-NAMA 2025 reference CSV.** Currently in `data/private/`; risk of accidental aggregation.
- **ADR-TBD — Abril 2026 data gap.** Either obtain the missing month or formally narrow the study to Q1 2026.
