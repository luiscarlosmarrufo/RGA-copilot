# Testing rules

Full plan: [docs/TESTING.md](../../docs/TESTING.md).

1. **Golden-number tests are the priority.** Every canonical metric has a hand-computed expected value tested against a small fixture.
2. **No live external APIs in CI.** Google Places, Pytrends, Anthropic — all mocked or recorded.
3. **One typed error → one test.** Every `DataParserError` subclass has a dedicated test with a fixture broken in exactly that way.
4. **Boundary tests on quadrants.** Median tie cases for menu engineering.
5. **Boundary tests on alerts.** Each threshold has below / at / above cases.
6. **Idempotency tests on persistence.** Re-uploading the same file yields the same rows.
7. **Failure isolation tests on enrichment.** Mock Places raising — financial endpoints still return 200.
8. **Prompt builder tests are deterministic.** Inputs X → prompt Y, character-for-character.
9. **Verifier tests.** Number-in-JSON cases pass; number-not-in-JSON cases flag.
10. **No NAMA data in fixtures.** `data/sample/` is anonymized or synthetic.
11. **Spanish snapshot tests for the UI.** A snapshot containing English fails.
12. **`make test-fast` exists** to run unit tests without integration/e2e for tight loops.
