# Google Places Strategy

Google Places is the **primary strategic differentiator** of RGA Financial Copilot. Anyone can compute margins; we layer local competitor intelligence on top.

## 1. What we extract

For each client sucursal (lat/lng known):

1. **Nearby competitors** within 1–3 km (configurable; default 1.5 km).
   - Filter by relevant `type` set: `restaurant`, `meal_takeaway`, `cafe`, plus client-specific tags.
2. **Per-place data:** name, address, rating, `user_ratings_total`, price_level, opening hours, `place_id`.
3. **Reviews** (latest available page; we paginate when API permits).
4. **Review velocity:** count of new reviews observed in the last 7 days, computed across refresh snapshots.
5. **Sentiment score:** percentage of reviews with rating ≥ 4 (deterministic, no LLM).
6. **Top topics:** simple keyword frequencies from review text (deterministic; LLM only when explicitly asked, never for numbers).
7. **Multilingual handling:** detect review language; keep raw text + language code. Translation for prompt context happens at prompt-build time, not at storage time.

## 2. Derived metrics (lives in `analytics.market`)

| Metric | Formula |
|---|---|
| Competitive index | `client_rating / mean(nearby_competitor_rating)` |
| Sentiment score | `share of reviews with rating >= 4` |
| Review velocity 7d | `count(new_reviews_in_last_7d)` |
| Rating drop alert | `rating(now) - rating(30d_ago) <= -0.2` |

All deterministic, computed in Python, persisted in Supabase. Never asked of Claude.

## 3. Caching and persistence

Places data is **always cached**. The cache lives in Supabase, not in-process.

| Table | Purpose | TTL |
|---|---|---|
| `places_searches` | search params + result IDs | 24h (configurable) |
| `places` | place metadata + rating/count snapshot | 24h refresh |
| `place_reviews` | individual reviews | append-only |
| `competitors` | curated client→place mapping | manual |

Refresh policy:

- **On-demand**: `POST /api/signals/refresh` with `places` source. If cache is still warm, served from cache.
- **Scheduled**: nightly refresh per client via the scheduler service.
- **Backoff**: exponential backoff on 429 / 5xx. Never retry tighter than 1 s.

## 4. Quota and cost discipline

- Google Places billing is per-request and per-field. Be deliberate about fields requested.
- A **daily quota guard** counts requests per API key and stops issuing calls past budget. The UI shows "Datos de mercado parciales" rather than failing.
- Use the cheapest field mask that satisfies the current view. Full review pulls are gated to scheduled jobs, never per-page-view.

## 5. Failure isolation

> Places failures must **not** break financial analysis.

Implementation:

- Places calls live in `enrich/places/`. They are **never** in the synchronous request path of `/api/upload`, `/api/clients/{id}/metrics`, or analytics computation.
- All callers handle `PlacesUnavailableError` and return `signals = null` for the affected sucursal.
- UI surfaces "Datos de mercado no disponibles" without removing financial cards.

## 6. Privacy / ToS posture

- We store `place_id`, public business names, and ratings — public data.
- Review text is stored only when permitted by Google's Terms of Service. Re-display in the UI follows attribution rules: original review author and source link.
- We do **not** scrape Google Maps outside the official Places API.
- Multilingual reviews are stored verbatim + language code; we never overwrite the original text.

## 7. Phase 4 deliverables (target)

- `enrich/places/client.py` — thin Google Places SDK wrapper with retries/backoff.
- `enrich/places/search.py` — nearby competitors per sucursal.
- `enrich/places/reviews.py` — review fetch + persistence.
- `analytics/market.py` — `competitive_index`, `sentiment_score`, `review_velocity_7d`.
- Migrations for `places_searches`, `places`, `competitors`, `place_reviews`.
- Scheduler job: `refresh_places_for_all_clients()` nightly.
- Tests with fixtures (no live API calls in CI).

## 8. Out of scope for Places (for now)

- Driving distance or isochrones.
- Photo intelligence.
- Booking / reservation integrations.
- Foot-traffic estimation beyond review velocity proxy.
