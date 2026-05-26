# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**RGA Financial Copilot / PHI OMEGA.** A financial copilot for hospitality / restaurant / event-driven food operations. It ingests Excel/CSV workbooks, computes deterministic financial analytics in Python, persists them in Supabase, enriches them with Google Maps Places signals, and uses Claude to **interpret** (never compute) the numbers into Spanish-language strategic recommendations.

Audience: RGA consultants from Tecnológico de Monterrey and the business owners they serve. First real client is Grupo NAMA — see [docs/context/Grupo_NAMA_Overview_RGA.md](docs/context/Grupo_NAMA_Overview_RGA.md).

## Non-negotiable rules

1. **Claude does not calculate financial metrics.** All math is in Python/Pandas. Claude receives precomputed JSON and produces prose.
2. **Spanish for the user.** UI, dashboard labels, alerts, reports, chat replies → Spanish. Code, comments, commit messages, engineering docs → English unless the user writes in Spanish.
3. **`BD 2026` is the source sheet.** Excel workbooks may contain many sheets. Never assume sheet index 0 is the transactional sheet. Resolve by sheet name `BD 2026` (case-insensitive, trimmed). If absent → raise `DataParserError`, never guess.
4. **No silent failures on data.** Missing essential columns, unparseable money, or malformed files raise typed errors. Never coerce-and-continue on financial inputs.
5. **Google Places is a primary differentiator.** Treat it as a first-class data source, not a nice-to-have. Cache + persist. Places API failures must degrade gracefully without breaking financial analysis.
6. **Pytrends is asynchronous only.** Never in the request path. Cron/scheduled cache only. Pytrends is fragile and not blocking for MVP.
7. **Phases are sequential.** Do not implement Phase N+1 work in a Phase N change. See [docs/TASKS.md](docs/TASKS.md).
8. **NDA data stays in `data/private/`.** Never commit, never paste, never log.

## Architecture in one diagram

```
Excel/CSV ──► Python parser (BD 2026 sheet) ──► Pandas analytics ──► Supabase tables
                                                       │
                                Google Places ─────────┼──► JSON for prompt
                                Pytrends (async) ──────┘
                                                       │
                                          Claude (interprets, in Spanish)
                                                       │
                                  Next.js dashboard / Markdown reports
```

Full diagram and table list in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## How to work in this repo

- **Engineering rules** are under [.claude/rules/](.claude/rules/) — read the relevant one before editing a layer.
- **Skills** under [.claude/skills/](.claude/skills/) are the canonical entry points for big actions (`plan-feature`, `implement-phase`, `validate-data-pipeline`, `review-google-places`, `review-anti-hallucination`, `prepare-deployment`).
- **Subagents** under [.claude/agents/](.claude/agents/) are named roles (architect, backend-engineer, frontend-engineer, data-engineer, financial-analyst, google-places-specialist, llm-guardrails-reviewer, test-engineer, devops-engineer). Delegate to them.
- **Decisions** go in [docs/DECISIONS.md](docs/DECISIONS.md) as ADRs. If you make an architectural choice not already recorded, add it before merging.
- **Tasks** live in [docs/TASKS.md](docs/TASKS.md). Update task status as work moves.

## Current phase

**Phase 0 — repository operating system.** No backend, frontend, parser, analytics, Places, Supabase, or Claude integration code exists yet. Phase 0 deliverable is the docs/rules/skills/agents structure plus environment and compose stubs.

Do not write application code until Phase 1 is opened in [docs/TASKS.md](docs/TASKS.md).

## Working with the source data

All client sales data lives in [data/private/](data/private/) (gitignored, NDA). The 2026 NAMA workbook is the study target; the 2025 file is a non-NAMA template — never aggregate them together.

Schema details, parsing gotchas (money formatting, ratio columns rendered as `$0.76`, accent handling, sparse `COSTO 1..50`), and required cleaning steps are in [docs/DATA_CONTRACTS.md](docs/DATA_CONTRACTS.md).

## What is intentionally absent

- No `pyproject.toml`, `package.json`, `Makefile`, or any other build/test config yet — those land in Phase 1.
- No `src/`, `tests/`, `frontend/`. Same reason.
- The repo's `.gitignore` currently has malformed heredoc lines (`cat > .gitignore <<'EOF'` and a trailing `EOF`) inherited from an earlier session; clean those when you next edit it.

If the user asks to run, lint, test, or build something that doesn't exist yet, refuse politely and point at the current phase in [docs/TASKS.md](docs/TASKS.md).
