---
name: review-anti-hallucination
description: Review LLM-touching code for compliance with the anti-hallucination guardrails. Verifies the 5-block prompt, the verifier, the Haiku memory-compression path, the Spanish constraint, and the citation requirements. Use before merging anything under llm/ or any prompt change.
---

# review-anti-hallucination

## When to use

- A PR modifies `llm/prompt.py`, `llm/verify.py`, `llm/compress.py`, or any prompt template.
- A new feature adds a Claude call.
- The user reports an LLM emitting a number that isn't in the JSON.

## Checklist

1. **5 immutable blocks** present and ordered: system, deterministic JSON, memory, market signals, user instruction.
2. **Block 2 source.** The JSON comes from `analytics/` outputs, not from anywhere else. The prompt builder rejects a missing block.
3. **Memory compression.** If memory > `LLM_MEMORY_TOKEN_BUDGET`, Haiku is invoked first in an isolated call that receives no financial JSON. The compressed memory is persisted before the primary call.
4. **System block in Spanish** and enforces:
   - No calculation.
   - Every number must appear verbatim in block 2 or 4.
   - Cited or canned response.
5. **Numeric verifier** runs on every response. Numbers absent from JSON are flagged or blocked.
6. **No chain-of-thought** is shown to the user. Routing chips come from the router.
7. **Citations rendered.** UI shows a citation chip for every numeric token.
8. **Sensitivity questions** ("if costs +5%") are routed to `analytics/sensitivity.py` first; the new JSON is reprompted.
9. **Audit log written.** `llm_insights` row: prompt hash, model id, output, citations, verifier result.
10. **No `print(prompt)`** or unsanitized logging of the user instruction — keep PII out of logs.
11. **Temperature ≤ 0.2** for production calls.
12. **Tests.** Verifier unit tests for both "number present" and "number absent" cases. Prompt builder tests are deterministic.

## Refusal cases

- A code path that lets Claude compute or estimate a number → refuse, route to Python.
- A prompt missing block 2 or 4 "because we don't have data yet" → refuse, supply empty-but-valid placeholders that the system block recognizes.
- Routing chips that include model tokens → refuse, replace with curated stage labels.

## Output shape

A reviewed checklist with file:line citations. Block the PR until verifier-related items pass.
