# Backend rules

Target stack (pending package-manager ADR): Python 3.12, FastAPI, Pandas, Pydantic v2, Supabase Python client, RQ (TBD).

1. **Pure analytics.** Anything in `rga/analytics/` is a pure function. No I/O, no DB calls, no API calls.
2. **Typed contracts.** Every public function has a Pydantic model or `pandas.DataFrame` with a documented schema. No untyped dicts at boundaries.
3. **Errors are typed.** `DataParserError` hierarchy for parser. `PlacesUnavailableError` for enrichment. Never return `None` to signal failure.
4. **No silent coercion of money.** Anywhere a monetary string is converted to float, an explicit parser is used. `try/except float()` is forbidden — raise a typed error instead.
5. **No business logic in route handlers.** Routes delegate to a service in `rga/services/`. Routes only do auth, validation, serialization.
6. **Background work via the queue.** Long jobs go to the worker. Pytrends is always async. Places is async unless cache hit.
7. **Idempotency by hash.** Re-uploading the same file produces the same rows. Use a stable hash of the file contents.
8. **Time zones.** Persist UTC. Render `America/Mexico_City` at the boundary.
9. **No print()**. Use the structured logger.
10. **Tests next to code.** `backend/tests/` mirrors `backend/rga/`. Golden tests in `backend/tests/golden/`.
