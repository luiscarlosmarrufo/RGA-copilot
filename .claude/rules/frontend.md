# Frontend rules

Target stack: Next.js (App Router), TypeScript strict, React Server Components allowed, Tailwind + CSS variables for the design tokens, server actions for mutations.

1. **Spanish only.** No English strings in components, even as placeholders. All copy comes from `app/i18n/es-MX.ts` (or equivalent). A lint rule should fail on bare ASCII English strings in JSX.
2. **No client-side financial math.** The UI displays numbers it receives from the API. Aggregations, percentages, deltas — already computed server-side.
3. **One insight per card.** Period. If two metrics belong together, design a new card type; do not stuff two.
4. **Design tokens.** Colors come from the palette in [docs/UI_SPEC.md](../../docs/UI_SPEC.md). Never hardcode hex values inside components.
5. **Citations are mandatory.** Every rendered number has a citation chip. A card without a citation is a bug.
6. **No chain-of-thought.** Streaming routing chips are allowed; raw model reasoning is not.
7. **Accessibility is not optional.** Focus rings on every interactive element. Contrast checked at build.
8. **No animations on numbers.** Numbers are read, not entertained. Subtle 100 ms fade on card mount is the ceiling.
9. **Server components first.** Client components only where interactivity demands it (chat surface, charts).
10. **Type the API client.** Generated or hand-rolled, but typed end-to-end.
