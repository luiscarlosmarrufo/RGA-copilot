# Data Contracts

This document is the single source of truth for what shape data takes as it moves through the system. The parser, analytics layer, persistence layer, and prompt builder must all conform to it.

## 1. Source workbook

### 1.1 Sheet resolution

- Source workbooks are **Excel (`.xlsx`)** or **CSV**. A workbook may contain many sheets.
- The transactional sheet is the one named **`BD 2026`** (case-insensitive, surrounding whitespace trimmed).
- **Never** assume the first sheet is the transactional sheet.
- If the workbook is `.csv`, treat the entire file as the `BD 2026` sheet.
- If `BD 2026` cannot be resolved → raise `DataParserError("missing BD 2026 sheet")`. Never silently fall back to another sheet.

### 1.2 Required columns

All of the following must be present (exact spelling, including accents) — case-insensitive on header match, but stored in canonical form:

| Column | Type | Notes |
|---|---|---|
| `MES` | string | e.g. `ENERO 2026`. Temporal grain. |
| `FECHA VENTA` | date or empty | Often empty; do not require non-null. |
| `LÍNEA DE NEGOCIO` | string | Sucursal code (`ANT`, `CAM`, `JUR`, `MOR`, `SOK`, …). |
| `SUBCATEGORÍA 1` | string | Family-level item category. |
| `SUBCATEGORÍA 2` | string | Item name. |
| `CANTIDAD` | int | Units sold. |
| `SUBTOTAL` | money → float | Pre-IVA revenue. |
| `TOTAL` | money → float | Post-IVA revenue. |
| `COSTO 1` | money → float | Primary cost component (almost always the only populated `COSTO N`). |
| `COSTO TOTAL SIN IVA` | money → float | Aggregate cost. |
| `COSTO TOTAL DEL SERVICIO` | money → float | Aggregate cost incl. service. |
| `UTILIDAD BRUTA` | money → float | Pre-computed in source; **recompute and compare**. |
| `MARGEN BRUTO` | ratio → float | Stored as `$0.76` style in source — strip `$`, keep as ratio. |
| `COL ESPECIAL 1` | string | Tag (e.g. `CALIENTE`). |
| `COL ESPECIAL 2` | string | Tag. |
| `COL ESPECIAL 3` | string | Tag. |
| `COL ESPECIAL 4` | string | Tag. |
| `COL ESPECIAL 5` | string | Tag. |
| `COL ESPECIAL 6` | string | Tag. |

If any required column is missing → `DataParserError("missing column: <name>")`.

Additional `COSTO 2`…`COSTO 50` columns may exist; they are read but typically sparse. Use them only when present and non-null.

### 1.3 Cleaning rules

Run in this order. Each step is unit-tested.

1. **Strip header whitespace** and normalize Unicode (NFC) for column names.
2. **Strip cell values** for string columns: leading asterisks (`*`), trailing periods (`.`), and surrounding whitespace.
3. **Money parsing.** For monetary columns: strip `$`, thousands `,`, surrounding quotes, then `float()`. Empty string → `NaN`.
4. **Ratio parsing.** `MARGEN BRUTO` has a `$` prefix in the source but is a ratio: strip `$`, then `float()`. Validate `0 ≤ value ≤ 1.5` (allow >1 only for rare loss-leader inversions — flag but don't reject).
5. **Drop `TOTAL == 0` rows** before computing margin averages or menu engineering aggregates. Keep them for raw audit views.
6. **Coerce `CANTIDAD` to int**, fail loudly if non-integer-castable.
7. **Trim and uppercase** sucursal codes in `LÍNEA DE NEGOCIO`.

Never silently coerce errors. Each cleaning step that drops or rewrites a row records a row-level note in a parser audit log returned alongside the cleaned DataFrame.

### 1.4 Typed errors

```
DataParserError                  ← base class
  MissingSheetError              ← BD 2026 not found
  MissingColumnError             ← required column absent
  MoneyParseError                ← cannot convert to float
  RatioOutOfRangeError           ← MARGEN BRUTO not in [0, 1.5]
  EncodingError                  ← non-UTF8 / accent corruption
```

All errors carry the file name, sheet name, row index, and column name when applicable.

## 2. Canonical metrics

These are the only places the listed quantities are computed. Each lives in `backend/rga/analytics/`.

| Metric | Formula | Function (target) |
|---|---|---|
| Utilidad bruta (recomputed) | `TOTAL - COSTO TOTAL DEL SERVICIO` | `analytics.margins.utilidad_bruta` |
| Margen bruto (recomputed) | `utilidad_bruta / TOTAL` (when TOTAL > 0) | `analytics.margins.margen_bruto` |
| Cost leakage | `COSTO TOTAL DEL SERVICIO - COSTO 1` (and ratio) | `analytics.margins.cost_leakage` |
| Sensitivity | metric under `costs * 1.05` | `analytics.sensitivity.shock_costs(0.05)` |
| Competitive index | `client_rating / mean(nearby_competitor_rating)` | `analytics.market.competitive_index` |
| Sentiment score | `% reviews with rating >= 4` | `analytics.market.sentiment_score` |
| Review velocity | new reviews in last 7 days | `analytics.market.review_velocity` |

When the source already provides `UTILIDAD BRUTA` and `MARGEN BRUTO`, the parser keeps both: the source value and the recomputed value. Discrepancies above a tolerance (e.g. 1%) are logged as data-quality flags but do not abort the run.

## 3. Menu engineering quadrants

Computed per `(sucursal, period)`. Inputs: per-item `volumen` (`CANTIDAD`) and `margen_unitario`.

| Quadrant | Spanish label | Rule |
|---|---|---|
| High vol / high margin | **Estrellas** | `volumen ≥ mediana_vol` and `margen ≥ mediana_margen` |
| High vol / low margin | **Caballos de Batalla** | `volumen ≥ mediana_vol` and `margen < mediana_margen` |
| Low vol / high margin | **Puzzles** | `volumen < mediana_vol` and `margen ≥ mediana_margen` |
| Low vol / low margin | **Perros** | `volumen < mediana_vol` and `margen < mediana_margen` |

Median is computed per sucursal-period to avoid cross-branch bias. Tie-break with strict `>=` against the median on the volume axis.

## 4. Alert thresholds

Centralized in `analytics.alerts`. Each alert has a severity (`INFO | MEDIUM | HIGH`) and a localized Spanish message template.

| Alert | Trigger | Severity escalation |
|---|---|---|
| Low margin | margin > 5pp below benchmark | `HIGH` if delta > 5pp |
| Profit concentration | one `COL ESPECIAL 1` item > 40% of profit | `HIGH` if > 50% |
| Inefficient business line | line margin > 2pp below mean of other lines | — |
| Maps rating drop | rating −0.2 in 30 days | — |
| Market trend rise | Trends term +30% in 4 weeks | — |

## 5. Persistence schema (overview)

Detailed DDL lands in Phase 3 migrations. Tables and the contracts they store:

| Table | Stores |
|---|---|
| `clients` | client metadata, default language `es-MX`, sucursales with lat/lng |
| `client_memory` | curated long-lived facts; token-counted |
| `uploaded_files` | file hash, name, size, sheet found, parser audit log |
| `financial_periods` | period (month) per client per sucursal |
| `analysis_runs` | one row per metric-computation job |
| `chat_messages` | role, content, routing chips |
| `external_signals` | umbrella for Places + Pytrends signals |
| `places_searches` | search params, radius, returned IDs |
| `places` | place_id, name, rating, review_count, last refreshed |
| `competitors` | client_id → place_id mapping (curated) |
| `place_reviews` | review text, language, rating, time |
| `llm_insights` | model, prompt hash, output, citations |
| `reports` | exported artifacts (PDF/MD) |

## 6. Deterministic JSON contract for the LLM

Block 2 of the 5-block prompt is a single JSON object. Two top-level metadata fields are mandatory on every result, propagated end-to-end from the parser (Phase 2):

- **`dataset_scope`** — string. Identifies which client + study the numbers belong to. Default and only-allowed-in-NAMA-runs value is `"nama_2026"`. The 2025 reference workbook is `"reference_2025"` and is never aggregated with NAMA data (ADR-0012). Analytics functions that consume a DataFrame call a `assert_nama_only` guard before computing; mixing scopes raises a typed error.
- **`period_coverage`** — object with `declared`, `actual`, and `missing` arrays of month strings (e.g. `"ENERO 2026"`). `declared` is the formally declared study window; `actual` is what the data contains; `missing = declared - actual`. When `missing` is non-empty, analytics emit a `missing_periods` warning that propagates to the UI, the report, and this prompt block. The model is instructed to treat missing months as absent — **never infer over them**. (ADR-0013)

Current declared window: `["ENERO 2026", "FEBRERO 2026", "MARZO 2026", "ABRIL 2026"]`. While Abril remains unavailable, the study is formally narrowed to Q1 2026 and `missing = ["ABRIL 2026"]` is surfaced on every result.

Block 2 shape (target — finalized in Phase 5):

```json
{
  "dataset_scope": "nama_2026",
  "period_coverage": {
    "declared": ["ENERO 2026", "FEBRERO 2026", "MARZO 2026", "ABRIL 2026"],
    "actual":   ["ENERO 2026", "FEBRERO 2026", "MARZO 2026"],
    "missing":  ["ABRIL 2026"]
  },
  "client": { "id": "...", "nombre": "Grupo NAMA" },
  "sucursales": [
    {
      "codigo": "ANT",
      "metrics": {
        "ventas_total": 1234567.89,
        "utilidad_bruta": 234567.89,
        "margen_bruto": 0.19,
        "menu_engineering": { "estrellas": 12, "caballos": 8, "puzzles": 15, "perros": 9 }
      },
      "alerts": [{ "code": "low_margin", "severity": "HIGH", "delta_pp": -7.2 }]
    }
  ],
  "market": {
    "ANT": { "competitive_index": 0.97, "sentiment_score": 0.71, "review_velocity_7d": 4 }
  },
  "warnings": [
    { "code": "missing_periods", "missing": ["ABRIL 2026"] }
  ]
}
```

Claude is told, in the system block, that **every number in its reply must come from this JSON**, and that **months in `missing` do not exist for the purposes of this conversation**.
