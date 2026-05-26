# LLM guardrails

Full design: [docs/ANTI_HALLUCINATION.md](../../docs/ANTI_HALLUCINATION.md).

1. **No arithmetic by Claude.** Every number in a response must be a verbatim copy from the deterministic JSON (block 2) or market signals (block 4).
2. **Five immutable blocks**, always in order:
   1. system instructions
   2. deterministic financial JSON
   3. client memory
   4. Google Places / market signals
   5. user instruction
   The prompt builder refuses to send incomplete or reordered prompts.
3. **Compress memory > `LLM_MEMORY_TOKEN_BUDGET`** using Haiku in a separate call that sees no financial JSON.
4. **Numeric verifier** runs on every response. Numbers absent from the JSON are flagged (Phase 5) or blocked + regenerated (Phase 9).
5. **Spanish responses only.** System block enforces `es-MX`. Reject responses that drift to English.
6. **Cited or canned.** Every numeric claim cites the JSON field that produced it. If the user asks for a number not in the JSON, reply with the canned: *"No tengo ese dato calculado; lo solicitaré al motor analítico."*
7. **No chain-of-thought exposure.** Routing chips (`Analizando margen`, etc.) come from the router, not from model output.
8. **Audit every run.** `llm_insights` row per call: prompt hash, model id, output, citations, verifier result.
9. **Temperature low (≤ 0.2)**, but treat as defense in depth. The verifier is the real guarantee.
10. **Sensitivity scenarios** ("if costs rise 5%") are routed back to `analytics/sensitivity.py` to produce new JSON; re-prompted with the new numbers. Claude never simulates math.
