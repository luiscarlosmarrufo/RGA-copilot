---
name: validate-data-pipeline
description: Validate the parser + analytics pipeline end-to-end against a fixture or a real (NDA-protected) workbook. Confirms BD 2026 sheet resolution, required columns, typed errors, cleaning rules, golden numbers, and JSON contract for the LLM. Use before declaring a parser/analytics PR ready, and after data-shape changes.
---

# validate-data-pipeline

## When to use

- A parser or analytics PR is up for review.
- The data shape changed (new column, new alert, new metric).
- A new client workbook is being onboarded and we need confidence the pipeline holds.

## How to run

1. **Sheet resolution.** Confirm `BD 2026` is found by name (case-insensitive, trimmed). Test the absent case → `MissingSheetError`.
2. **Required columns.** Confirm all required columns from [docs/DATA_CONTRACTS.md](../../../docs/DATA_CONTRACTS.md) § 1.2 are present. Drop one in a fixture → `MissingColumnError`.
3. **Money parsing.** For each monetary column, confirm `"$1,234.56"` parses and `"abc"` raises `MoneyParseError`.
4. **`MARGEN BRUTO`.** Confirm the `$0.76`-as-ratio parsing path. Out-of-range → `RatioOutOfRangeError`.
5. **Cleaning order.** Confirm asterisks/periods are stripped, NFC normalization is applied, accented headers resolve.
6. **`TOTAL == 0` dropped** before margin aggregates, kept for raw audit.
7. **`CANTIDAD` integer cast** fails loudly on non-integer-castable input.
8. **Sucursal uppercased and trimmed.**
9. **Golden numbers.** Compare every analytics output against the hand-computed expected value for the fixture.
10. **Recomputed vs source.** Compare recomputed `UTILIDAD BRUTA` / `MARGEN BRUTO` to source-provided values within tolerance. Discrepancies are flagged, not silenced.
11. **LLM JSON contract.** Confirm the produced JSON matches the shape in [docs/DATA_CONTRACTS.md](../../../docs/DATA_CONTRACTS.md) § 6.

## Refusal cases

- A request to validate against NAMA data without an anonymized fixture path → refuse, ask to anonymize first or use existing `data/sample/` fixtures.
- A request to "skip the typed error for now" → refuse. Typed errors are non-negotiable.

## Output shape

A pass/fail checklist per step above, with the row index + column for any failure. If any step fails, the pipeline is not validated.
