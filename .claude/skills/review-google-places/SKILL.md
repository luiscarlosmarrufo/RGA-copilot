---
name: review-google-places
description: Review a PR or design that touches the Google Places integration. Checks caching, quota guard, backoff, failure isolation, ToS compliance, and that derived metrics live in Python — not in Claude. Use before merging anything under enrich/places/ or analytics/market.py.
---

# review-google-places

## When to use

- A PR modifies `enrich/places/`, `analytics/market.py`, or the Places-related migrations.
- A design proposes a new use of the Places API.

## Checklist

1. **Cache-first reads.** Code paths consult Supabase (`places_searches`, `places`, `place_reviews`) before calling the API.
2. **TTL respected.** Refresh only on cache miss or when TTL has expired.
3. **Field mask discipline.** Only the fields needed for the call are requested. Full review pulls are gated to scheduled jobs.
4. **Quota guard wired in.** A daily counter blocks calls past budget. The UI degrades to "Datos de mercado parciales".
5. **Backoff.** Exponential with jitter on 429/5xx. Never retry tighter than 1 s.
6. **Failure isolation.** No Places call sits in the synchronous request path of analytics. Callers catch `PlacesUnavailableError` and continue.
7. **No LLM math.** `competitive_index`, `sentiment_score`, `review_velocity` are all in `analytics/market.py`. The LLM only reads them.
8. **Reviews verbatim.** Original text + language code preserved. No translation at storage time.
9. **ToS / attribution.** UI displays author and source link for any rendered review.
10. **No scraping.** Only the official Places API.
11. **place_id is the key.** Joins/audit use `place_id`, never name.
12. **Tests.** No live API in CI. Recorded fixtures or mocks. Failure-isolation test present.

## Refusal cases

- A design that queries Places inside `/api/upload` or `/api/clients/{id}/metrics` synchronously → refuse.
- A design that asks Claude to compute a market metric → refuse and move the math to `analytics/market.py`.
- A change that removes the quota guard "for now" → refuse.

## Output shape

A reviewed checklist, with file:line citations for each issue. Block the PR until all blocking items pass.
