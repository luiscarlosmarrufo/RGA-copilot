# RGA Financial Copilot / PHI OMEGA

Financial copilot for hospitality businesses, restaurants, and event-driven food operations. Transforms messy Excel/CSV financial data into **deterministic** financial analytics, connects those analytics with **local market intelligence** from Google Maps Places, and produces **Spanish-language** strategic recommendations for RGA consultants and business owners.

> The user-facing product, UI, reports, dashboard labels and business copy are in **Spanish**. Code and engineering docs stay in English.

---

## Core architecture rule

```
Python calculates.
Supabase persists.
Google Places contextualizes.
Claude interprets.
```

Claude **never** performs financial arithmetic. All numbers are computed by Python/Pandas, persisted in Supabase, and handed to Claude as already-computed JSON.

---

## Repository layout (Phase 0)

```
RGA-copilot/
├── README.md                 ← this file
├── CLAUDE.md                 ← operating instructions for Claude Code
├── .env.example              ← required environment variables, no real values
├── docker-compose.yml        ← production-shaped compose (placeholders)
├── docker-compose.dev.yml    ← local dev overrides
│
├── data/
│   ├── private/              ← NDA-protected client data (gitignored)
│   └── sample/               ← anonymized fixtures safe to commit
│
├── docs/                     ← the product/architecture/contract specs
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACTS.md
│   ├── API_SPEC.md
│   ├── UI_SPEC.md
│   ├── GOOGLE_PLACES_STRATEGY.md
│   ├── ANTI_HALLUCINATION.md
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   ├── DECISIONS.md          ← ADRs
│   └── TASKS.md              ← phased task tracker
│
└── .claude/
    ├── rules/                ← always-on engineering rules
    ├── skills/               ← invokable skills (plan-feature, implement-phase, …)
    └── agents/               ← named subagents (architect, backend-engineer, …)
```

No `src/`, `tests/`, `frontend/`, or any application code exists yet. **This is intentional.** Phase 0 builds only the repository operating system. See [docs/TASKS.md](docs/TASKS.md) for the phased plan.

---

## Phases

| Phase | Scope | Status |
|------:|---|---|
| **0** | Repo OS — docs, rules, skills, agents, env/compose stubs | **current** |
| 1 | Backend skeleton + Excel/CSV parser | pending |
| 2 | Deterministic analytics (margins, menu engineering, alerts) | pending |
| 3 | Supabase persistence layer | pending |
| 4 | Google Places intelligence | pending |
| 5 | LLM prompt builder (5 immutable blocks) | pending |
| 6 | Frontend dashboard (Bloomberg/Palantir aesthetic, Spanish) | pending |
| 7 | Report generation | pending |
| 8 | Docker / deploy readiness | pending |
| 9 | Hardening | pending |

Do not skip phases. Do not begin a phase before the previous is signed off in [docs/DECISIONS.md](docs/DECISIONS.md).

---

## Getting started (Phase 0)

There is nothing to install or run yet. To work on the repo OS:

1. Read [CLAUDE.md](CLAUDE.md).
2. Read [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
3. Review the engineering rules under [.claude/rules/](.claude/rules/).
4. Check [docs/TASKS.md](docs/TASKS.md) for the Phase 1 entry criteria.

---

## Confidentiality

`data/private/` contains client data under NDA. It is gitignored and must never be:

- Committed to git.
- Pasted into PR descriptions, issues, screenshots, or chat with third-party tools.
- Uploaded to public LLMs, pastebins, or diagram renderers.
- Included in error logs or telemetry.

See [.claude/rules/security.md](.claude/rules/security.md) and [docs/ANTI_HALLUCINATION.md](docs/ANTI_HALLUCINATION.md).
