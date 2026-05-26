---
name: plan-feature
description: Plan a new feature within the four-layer architecture and the current phase. Produces a phased task list, identifies the touched layers (Python/Supabase/Places/Claude), lists the ADRs required, and the tests that must be added. Use when the user proposes a new capability or changes the scope of an existing one.
---

# plan-feature

## When to use

- The user describes a new product capability.
- The user asks "how would we add X?"
- Scope of an existing feature is changing materially.

Do not use for bug fixes that don't change scope.

## How to run

1. **Anchor the request to a phase.** Identify which phase in [docs/TASKS.md](../../../docs/TASKS.md) this feature belongs to. If it crosses phases, split it.
2. **Map to the four layers.** For each of Python / Supabase / Google Places / Claude, state whether the feature touches that layer and how. Refuse designs where Claude is asked to compute.
3. **Identify the data contract changes.** Does this require new columns, new tables, or a new shape in the deterministic JSON? Cross-reference [docs/DATA_CONTRACTS.md](../../../docs/DATA_CONTRACTS.md).
4. **List ADRs needed.** Any architectural choice not already in [docs/DECISIONS.md](../../../docs/DECISIONS.md) → propose a new ADR with title and key question.
5. **Sketch tests first.** Golden-number test cases, parser error cases, and (if applicable) verifier cases for the LLM. No design without tests.
6. **Produce a task list** of small, sequenced PRs. Each PR ≤ ~400 lines of diff. Each PR has a clear "done" definition.
7. **Spanish UI copy.** If the feature surfaces in the UI, draft the Spanish strings as part of the plan, not after.

## Output shape

A markdown plan with:

- **Feature.** One sentence.
- **Phase / layer matrix.** Table.
- **Data contract changes.** Bullet list.
- **ADRs needed.** Numbered list with one-line question each.
- **Tests to add.** Bullet list grouped by file.
- **PR sequence.** Numbered list with titles and "done" criteria.
- **Open questions for the user.** ≤ 5, sharp.

## Refusal cases

- A feature whose plan asks Claude to compute numbers → refuse and propose a Python equivalent.
- A feature that puts Pytrends in the request path → refuse and propose a scheduled-cache equivalent.
- A feature that adds English UI copy → refuse and rewrite in Spanish.
