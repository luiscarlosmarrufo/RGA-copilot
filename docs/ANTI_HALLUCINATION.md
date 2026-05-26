# Anti-Hallucination Guardrails

The single most expensive failure mode of this product is **Claude inventing or recomputing a number.** This document lists the guardrails that make that mode impossible-by-construction, not merely discouraged by prompt.

## 1. Core invariant

> **Claude never performs financial arithmetic.**

If a numeric figure appears in a Claude response, it must be a verbatim copy from the deterministic JSON block of the prompt. No additions, no subtractions, no averages, no rounding-other-than-display, no "approximately".

## 2. The 5-block prompt

Every call to Claude uses exactly these blocks, in this order. The builder refuses to send a request that is missing or out of order.

1. **System instructions** — role, language (Spanish), refusal rules, formatting rules.
2. **Deterministic financial JSON** — the only source of numbers Claude is allowed to cite.
3. **Client memory** — curated long-lived facts (compressed if > `LLM_MEMORY_TOKEN_BUDGET`).
4. **Google Places / market signals** — competitor data, sentiment, review velocity.
5. **User instruction** — the actual question / task.

Blocks 2 and 4 are pre-computed by Python. Claude does not transform them; it reads and cites.

## 3. System-block guardrails (verbatim spirit)

The system block says, in Spanish:

- Tu rol es interpretar números, no calcularlos.
- Toda cifra de tu respuesta debe aparecer textualmente en el bloque 2 (financiero) o 4 (mercado).
- No realices sumas, restas, promedios, porcentajes o redondeos.
- Si te piden una cifra que no está en los bloques 2 o 4, responde: "No tengo ese dato calculado; lo solicitaré al motor analítico."
- Responde siempre en español.
- Cita la fuente de cada cifra (nombre del campo en el JSON).

## 4. Memory compression

- Memory > `LLM_MEMORY_TOKEN_BUDGET` (default 6,000) is **first** compressed by Haiku in a separate, isolated call whose only job is summarization.
- The compression call receives no financial JSON. It cannot accidentally bake numbers into memory.
- Compressed memory is stored as a new `client_memory` row with `compressed_from` pointing to source ids.

## 5. Numeric verification step

Before a Claude response is returned to the user:

1. Run a regex extractor over the response to enumerate all numeric tokens (currency, percentages, counts).
2. Cross-check each token against the deterministic JSON (block 2/4) using exact string match or a tolerant numeric match (±0.001 absolute, ±0.1% relative).
3. If any token is not found → flag the response. In Phase 5 we surface a warning; in Phase 9 the response is blocked and regenerated with stronger instructions.

This is implemented in `llm/verify.py` (Phase 5 target).

## 6. UI guardrails

- Every number rendered in the UI carries a citation chip pointing to its metric source (Python function + row count).
- Claude responses render with citation chips per number. A response without citations is shown with a soft warning banner.
- Streaming responses do not display until at least one citation is attached.

## 7. Routing chips ≠ chain of thought

The UI streams routing chips (`Analizando margen`, `Consultando memoria`, `Redactando`). These are emitted by the **router**, not by Claude. They describe which pipeline stages ran. Internal Claude reasoning is never displayed.

## 8. What we do NOT rely on

- Prompting the model to "be careful with math". Necessary but insufficient.
- Temperature 0. We set it low but treat it as defense in depth.
- Asking the model to "double-check itself". Verification is deterministic, in Python.

## 9. Failure surface and what to do

| Symptom | Action |
|---|---|
| Number in reply not in JSON | Verifier flags or blocks; regenerate with stricter system block. |
| Model attempts arithmetic anyway | Treat as a guardrail bug; add the case to `llm/tests/test_no_arithmetic.py`. |
| Memory grew unbounded | Trigger `POST /api/memory/compress`; review what is being written to memory. |
| Places snapshot stale | Refresh signal; never have the LLM "estimate" market data. |
| User asks for a number we don't have | Reply with the canned: *"No tengo ese dato calculado; lo solicitaré al motor analítico."* |

## 10. Audit log

Every Claude run persists to `llm_insights`:

- prompt hash (per block)
- model id + version
- raw output
- extracted citations
- verifier result (pass / flagged / blocked)
- correlation id

This is what makes responses **reproducible and reviewable**.
