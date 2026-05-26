# Google Places rules

Full strategy: [docs/GOOGLE_PLACES_STRATEGY.md](../../docs/GOOGLE_PLACES_STRATEGY.md).

1. **Places is a first-class data source**, not a nice-to-have. Treat it as core to the product.
2. **Cache everything.** Reads first hit Supabase (`places_searches`, `places`, `place_reviews`). The API is called only on cache miss or scheduled refresh.
3. **Default radius**: `PLACES_DEFAULT_RADIUS_METERS` (default 1500 m). Per-call override allowed within 1–3 km.
4. **Field discipline.** Use the smallest field mask that answers the current question. Full review pulls are scheduled jobs only.
5. **Quota guard.** A daily counter per API key. Past budget → stop issuing calls, surface "Datos de mercado parciales" in the UI. Do not pay surprise bills.
6. **Backoff.** Exponential on 429 / 5xx with full jitter. Never retry tighter than 1 s.
7. **Failure isolation.** Places **never** sits in the synchronous request path of analytics. Callers catch `PlacesUnavailableError` and continue.
8. **Reviews are stored verbatim with language code.** No translation at storage time. Translation, if needed, happens during prompt building.
9. **Sentiment / competitive index / review velocity** are computed in Python. Never asked of Claude.
10. **No scraping.** Only the official Places API. Respect Google's attribution and display rules for reviews.
11. **Curated competitor list.** The `competitors` table is a curated client→place mapping. Nearby search seeds it; humans approve.
12. **Place IDs are stable.** Keys, joins, and audit references use `place_id`, not name.
