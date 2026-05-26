# API Spec

All routes are mounted under `/api`. Server: FastAPI (target). Auth: Supabase JWT in `Authorization: Bearer …`. Content-type defaults to `application/json` except `/upload`.

## Conventions

- Spanish strings only at the boundary that talks to the UI; internal error codes are English snake_case.
- Errors use a uniform envelope:
  ```json
  { "error": { "code": "data_parser_error", "message": "Hoja BD 2026 no encontrada", "details": {...} } }
  ```
- All list endpoints support `?limit` and `?cursor` for pagination.
- Times are ISO-8601 in UTC; the UI converts to `America/Mexico_City`.

---

## `GET /api/health`

Liveness + readiness. Public.

**200**
```json
{ "status": "ok", "version": "0.0.0", "supabase": "ok", "redis": "ok" }
```

Each downstream is checked with a short timeout; degraded dependencies yield `"status": "degraded"` and `200` (the API itself is up).

---

## `POST /api/upload`

Multipart upload of an `.xlsx` / `.csv` workbook for a client.

**Request (multipart/form-data)**
- `client_id` (uuid, required)
- `file` (binary, required, ≤ `UPLOAD_MAX_MB`)
- `period_hint` (string, optional — e.g. `"2026-Q1"`)

**202 — accepted, processing**
```json
{
  "uploaded_file_id": "uuid",
  "analysis_run_id": "uuid",
  "sheet_resolved": "BD 2026",
  "rows": 8101,
  "warnings": [{ "code": "ratio_clamped", "row": 412, "column": "MARGEN BRUTO" }]
}
```

**4xx errors** are typed parser errors:
- `missing_sheet` (`BD 2026` not found)
- `missing_column`
- `money_parse_error`
- `ratio_out_of_range`
- `encoding_error`

The endpoint runs the parser synchronously (it is fast) and enqueues the heavier analytics + enrichment work to a worker. Status is polled via `GET /api/clients/{client_id}/metrics?run=...`.

---

## `POST /api/chat`

Conversational entry point. Always runs through the 5-block prompt builder.

**Request**
```json
{
  "client_id": "uuid",
  "message": "¿Qué platillos están canibalizando el margen en Antea?",
  "session_id": "uuid?"
}
```

**Response (streaming, SSE)** — events:
- `routing` — `{ "chips": ["Analizando margen", "Consultando memoria", "Redactando"] }`
- `delta` — partial text chunks (Spanish).
- `citations` — `{ "metrics": [...], "memory_ids": [...], "places": [...] }`
- `done`

The router emits chips for the UI's optimistic "Pensando…" state but never reveals chain-of-thought.

---

## `POST /api/signals/refresh`

Force a refresh of external signals for a client.

**Request**
```json
{ "client_id": "uuid", "sources": ["places", "pytrends"] }
```

**202**
```json
{ "jobs": [{ "source": "places", "job_id": "..." }, { "source": "pytrends", "job_id": "..." }] }
```

Pytrends always returns `202` — never blocks. Places may run synchronously if the cache is warm; otherwise enqueued.

---

## `POST /api/memory/compress`

Compress a client's memory if it exceeds `LLM_MEMORY_TOKEN_BUDGET`.

**Request** `{ "client_id": "uuid" }`

**200**
```json
{ "before_tokens": 7421, "after_tokens": 2980, "compressed_with": "haiku" }
```

Idempotent; if already under budget, returns `{ "skipped": true }`.

---

## `GET /api/clients/{client_id}/metrics`

Deterministic metrics for the client. The shape mirrors the JSON contract in [DATA_CONTRACTS.md](DATA_CONTRACTS.md) § 6.

Query params:
- `run` (uuid, optional) — specific run; default is latest completed.
- `period` (e.g. `2026-01`) — optional filter.

**200** — the canonical metrics JSON.

---

## `GET /api/clients/{client_id}/signals`

Returns the latest Places + Pytrends snapshot for the client.

**200**
```json
{
  "places": {
    "ANT": {
      "competitive_index": 0.97,
      "sentiment_score": 0.71,
      "review_velocity_7d": 4,
      "competitors": [{ "place_id": "...", "name": "...", "rating": 4.5 }]
    }
  },
  "pytrends": {
    "fetched_at": "...",
    "terms": [{ "term": "sushi querétaro", "delta_4w_pct": 32.1 }]
  }
}
```

Pytrends may be `null` if the cache hasn't been populated yet — the UI shows "Datos de mercado no disponibles" gracefully.

---

## `GET /api/clients/{client_id}/reports`

Lists generated reports (Phase 7).

**200**
```json
{ "reports": [{ "id": "uuid", "format": "pdf", "created_at": "...", "url": "signed-url" }] }
```

---

## Status codes

- `200` — success.
- `202` — accepted; long-running work enqueued.
- `400` — typed parser/validation error.
- `401` — missing/invalid JWT.
- `403` — RLS denied.
- `404` — client or run not found.
- `409` — duplicate file hash on upload.
- `422` — semantic validation (e.g. malformed `period`).
- `429` — rate-limited.
- `500` — internal; always logged with a correlation id.

## Rate limits (Phase 9 target)

- `/api/chat`: 30 req/min/user.
- `/api/upload`: 10 req/min/user.
- `/api/signals/refresh`: 5 req/min/client.
- Everything else: 120 req/min/user.
