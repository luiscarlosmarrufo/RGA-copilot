# Architecture rules

These are non-negotiable. When in conflict with anything else, these win.

1. **Four-layer rule.** Python calculates. Supabase persists. Google Places contextualizes. Claude interprets. Never let a layer skip its predecessor. Never let Claude compute a number.
2. **Phased delivery.** Do not write Phase N+1 code in a Phase N change. See [docs/TASKS.md](../../docs/TASKS.md).
3. **`BD 2026` is the canonical sheet.** Resolve by name (case-insensitive, trimmed). Never assume the first sheet.
4. **Fail loud on data, soft on enrichment.** Parser errors abort. Places / Pytrends outages degrade signals only.
5. **Spanish at the user boundary; English in code.** UI strings live in an i18n catalog. Logs, error codes, ADR titles in English.
6. **Determinism.** Analytics functions are pure `(DataFrame, params) → metrics`. Reproducible.
7. **No dead layers.** If you add a module, wire it through the API + UI in a follow-up task. No orphaned subsystems.
8. **One ADR per architectural choice.** Add to [docs/DECISIONS.md](../../docs/DECISIONS.md) before merging the choice.
