---
name: implement-phase
description: Execute the deliverables of the current phase in TASKS.md. Verifies entry criteria, sequences the work in small PR-sized chunks, and stops at the phase's exit criteria. Use to drive Phase 1 → Phase 9 work.
---

# implement-phase

## When to use

- The user says "start Phase N" or "let's implement Phase N".
- Phase N's entry criteria are met in [docs/TASKS.md](../../../docs/TASKS.md).

Do not use to jump phases, do parallel phases, or skip exit criteria.

## How to run

1. **Verify entry criteria.** Read the phase in [docs/TASKS.md](../../../docs/TASKS.md). If any entry box is unchecked, stop and report which.
2. **Re-read the rules.** Load the relevant `.claude/rules/*.md` for the phase's layer(s).
3. **Sequence the deliverables.** Order them so each PR can be merged independently. Parser before analytics, analytics before persistence, persistence before enrichment, etc.
4. **For each deliverable:**
   - Open a TodoWrite item.
   - Write tests first when the layer is determinism-critical (parser, analytics, prompt builder, verifier).
   - Implement.
   - Update [docs/TASKS.md](../../../docs/TASKS.md) by checking the box.
5. **Verify exit criteria** at the end of the phase. If any are unmet, do not declare phase complete.
6. **Update [docs/DECISIONS.md](../../../docs/DECISIONS.md)** for any architectural choices made along the way.

## Phase-specific guardrails

- **Phase 1**: never broaden the parser to handle non-`BD 2026` sheets. Every parser error must be typed.
- **Phase 2**: analytics are pure functions. No I/O. No DB access.
- **Phase 3**: every metric written has a corresponding read path and a test for both.
- **Phase 4**: no Places call in a synchronous endpoint. Cache first.
- **Phase 5**: prompt builder rejects any call missing one of the 5 blocks. Verifier ships with the builder, not after.
- **Phase 6**: every number rendered carries a citation chip. Spanish-only lint enabled.
- **Phase 7**: report numbers must equal dashboard numbers byte-for-byte at the same precision.
- **Phase 8**: Dockerfiles do not embed secrets or client data.
- **Phase 9**: RLS audit before declaring done.

## Refusal cases

- Entry criteria unmet → refuse, list what's missing.
- A deliverable would force a layer to skip its predecessor → refuse, redesign.
- Phase N+1 work attempted in a Phase N PR → split the PR.

## Output shape

Per session:
- A short status line: which phase, which deliverable, what's next.
- After each PR: which checkbox in [docs/TASKS.md](../../../docs/TASKS.md) just flipped, link to the diff.
