# REVIEW — django-traceid documentation pass

Documentation-only review. No source, tests, deps, CI, or config were changed.

## Contradictions found (report only — not fixed)

1. **Branch model / default branch mismatch.**
   - `CLAUDE.md`: default branch `main`; branch prefixes `feat/ fix/ chore/ docs/`.
   - `AGENTS.md`: default branch `develop`; branch prefixes `feature/ bugfix/ chore/ hotfix/ release/`.
   - The repo currently sits on `chore/claude-config-drift-hook` (git). Owner should pick one.

2. **"Moving parts / lines" count mismatch.**
   - `README.md`: "5 moving parts, ~90 lines".
   - `CLAUDE.md`: "6 moving parts, ~190 statements".
   - Actual runtime modules with logic: 6 (`context, middleware, filters, conf, rq, apps`).

3. **Python floor phrasing.** README/CLAUDE say "3.12–3.14" / "3.12+"; `pyproject.toml`
   classifiers list 3.12/3.13/3.14 and Django 4.2–5.2. Consistent, but the exact
   `requires-python` string was not surfaced here — confirm it reads `>=3.12` (UNKNOWN exact value).

## Documentation debt / gaps

- No ADR records on disk (`handover.md` lists ADRs as "not available"); DECISIONS.md here is a
  reconstruction. If canonical ADRs exist in `shared-standards`, link them.
- Notion links and repo profile/DDD level are "not available" in generated `handover.md`.
- Exact current test-coverage percentage not re-measured (85% gate only).
- Celery/MQTT propagation documented but not exercised by the in-repo test suite.

## Existing docs preserved

`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, `ai-instructions.md`,
`handover.md`, `legal/*`, `docs/*`, `graphify-out/*` were left untouched. New root docs complement
them (ARCHITECTURE, REQUIREMENTS, CONSTRAINTS, DECISIONS, TESTING, SECURITY, OBSERVABILITY,
GLOSSARY, this REVIEW).

## Docs deliberately skipped

- **PRD.md** — thin/no product-management material in-repo; purpose is fully covered by README +
  ARCHITECTURE. Skipped to avoid fabrication.
- **TRD.md** — would duplicate ARCHITECTURE + REQUIREMENTS + CONSTRAINTS for a ~200-statement
  library; folded into those instead.
- **ROADMAP.md** — no forward-looking backlog found in-repo (CHANGELOG `[Unreleased]` empty).
  Skipped to avoid inventing plans.
