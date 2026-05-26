# Product Spec — RGA Financial Copilot / PHI OMEGA

## 1. Purpose

A financial copilot for hospitality businesses (restaurants, food halls, event-driven food operations). It turns the messy Excel/CSV workbooks that consultants actually receive into deterministic financial analytics, blends them with **local market intelligence** from Google Maps Places, and emits Spanish-language strategic recommendations.

Primary users:

- **RGA consultants** (Tecnológico de Monterrey teams producing Reportes de Gestión Aplicada).
- **Business owners** of the analyzed company (read-only consumer of the dashboard and reports).

First real client: **Grupo NAMA** (Querétaro, Japanese restaurants, 4 NAMA sucursales + Soko Teppan).

## 2. Product principles

1. **Numbers are sacred.** Every figure in the UI traces back to a Python function operating on raw client data. No LLM-generated numbers.
2. **One insight per card.** The dashboard rewards scanability. Density without noise.
3. **Spanish, always.** UI copy, alerts, report prose. English is for engineers only.
4. **Local market context is the differentiator.** Anyone can compute margins; we layer Google Places competitor intelligence on top.
5. **Fail loud on data, fail soft on enrichment.** A malformed workbook stops the run. A Places outage degrades gracefully.

## 3. Core user journeys

### 3.1 Consultor — onboarding a client

1. Create client record (nombre, sucursales con coordenadas).
2. Upload one or more Excel/CSV workbooks containing the `BD 2026` sheet.
3. System parses, validates, computes deterministic metrics, persists.
4. System enriches with Google Places (competidores 1–3 km, ratings, reviews).
5. System asks Claude for a Spanish executive summary using the 5-block prompt.
6. Consultor reviews the dashboard, edits client memory, exports the report.

### 3.2 Consultor — diagnostic chat

1. Open a client.
2. Ask a question in Spanish (e.g. *"¿Qué platillos están canibalizando el margen en Antea?"*).
3. UI shows a "Pensando…" optimistic state with semantic routing chips (e.g. *Analizando margen* → *Consultando memoria* → *Redactando*).
4. Reply cites: metric source rows, memory entries, Places signals.

### 3.3 Owner — dashboard

1. Login (read-only role).
2. Sees atomic insight cards, semaphore status, top alerts.
3. Cannot upload or edit memory.

## 4. Feature scope by phase

| Phase | Feature |
|---|---|
| 1 | Excel/CSV parser keyed on `BD 2026`, typed errors |
| 2 | Margins, menu engineering quadrants, alerts |
| 3 | Supabase persistence of clients, files, periods, runs, memory |
| 4 | Google Places competitor search, ratings, sentiment, review velocity |
| 5 | 5-block prompt builder, Haiku compression of long memory |
| 6 | Next.js dashboard (Corporate Luxury aesthetic) |
| 7 | Spanish PDF/Markdown report generation |
| 8 | Docker images, deploy pipeline, health checks |
| 9 | Hardening: rate limits, observability, RLS audit |

## 5. Out of scope (for now)

- Multi-tenant billing.
- Real-time POS integrations.
- Mobile-native apps.
- Predictive ML beyond simple sensitivity analysis.
- Non-Spanish UI.

## 6. Success criteria

- A consultor can go from raw NAMA workbook to a signed-off Spanish executive summary in under 30 minutes.
- Every number in that summary is traceable to a Pandas function and a stored Supabase row.
- Google Places signals appear in at least one card per sucursal.
- Zero LLM-emitted figures.
