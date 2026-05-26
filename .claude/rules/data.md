# Data rules

Single source of truth for these rules: [docs/DATA_CONTRACTS.md](../../docs/DATA_CONTRACTS.md). What follows are the do/don't enforcement notes.

1. **Resolve `BD 2026` by name.** Never by index. Case-insensitive, trimmed.
2. **Required columns** must all be present (see DATA_CONTRACTS § 1.2). Any missing → `MissingColumnError`.
3. **Money parsing** strips `$`, thousands `,`, surrounding quotes, then `float()`. Empty → `NaN`. Garbage → `MoneyParseError`.
4. **`MARGEN BRUTO` is a ratio**, despite the `$` prefix. Parse, then validate `0 ≤ x ≤ 1.5`. Out of range → `RatioOutOfRangeError`.
5. **String cleaning**: strip leading `*` and trailing `.`, then `.strip()`. Normalize to Unicode NFC.
6. **Drop `TOTAL == 0`** before margin/quadrant aggregates. Keep them for raw audit views.
7. **`CANTIDAD` is an integer.** Non-integer-castable → fail loudly.
8. **Sucursal codes** uppercased and trimmed.
9. **Never aggregate the 2025 reference CSV with NAMA data.** They are not the same client.
10. **Parser audit log.** Every cleaning step that drops or rewrites a row records a row-level note returned alongside the cleaned DataFrame. The UI shows these as `warnings` after upload.
11. **No silent fallbacks.** If you're tempted to "try the second sheet" or "default to 0", stop and raise a typed error.
12. **Never write client data outside `data/private/`** during development. Tests use `data/sample/` only.
