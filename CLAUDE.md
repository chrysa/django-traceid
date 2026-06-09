# CLAUDE.md — django-traceid

> @[claude-sonnet-4-6]
> **Claude Code**: also read `.github/copilot-instructions.md` and any `.github/instructions/*.instructions.md`.
> For Django rules see `shared-standards/copilot-instructions/django.md`.

## Project

**Name:** django-traceid
**Stack:** Python 3.12–3.14 · Django library (zero runtime dependency beyond Django; `rq` optional)
**Purpose:** End-to-end trace / request-id propagation for Django — project-agnostic, zero-config,
no monkey-patching. Every log line emitted while handling a request carries the same `trace_id`
(HTTP → services → ORM → background jobs → pub/sub), retraceable with one query in Loki/Kibana/Sentry.

## Layout

Flat package `django_traceid/` (~90 lines of runtime code, 5 moving parts):

```
django_traceid/
  middleware.py  # extracts/generates X-Request-ID, sets it in context, echoes on response
  context.py     # contextvar holding the current trace_id
  filters.py     # logging filter that injects trace_id into every record
  conf.py        # settings surface (header name, propagation toggles)
  apps.py        # AppConfig wiring
  rq.py          # optional: trace_id propagation across RQ background jobs
tests/           # pytest-django suite
```

## Conventions

- Language: English — all code, comments, docs, and config files.
- Commits: Conventional Commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`).
- Branches: `feat/`, `fix/`, `chore/`, `docs/`. Default branch: `main`.
- Supports Python 3.12+ (library); CI tests on 3.14. `requires-python` floor is intentional.

## Standards

- Max function lines: 50 · Max file lines: 500 · Lint warnings: 0
- Test coverage: ≥ 85% · `mypy --strict` clean · full type annotations on the public API

## Setup

```bash
make install      # install dev deps + pre-commit
make lint         # ruff
make typecheck    # mypy
make test         # unit tests
make test-cov     # tests + coverage
make build        # build wheel
```

All checks run via `make` or `pre-commit` only — never invoke linters/tests directly on the host.

## CI

- Runs on push to `main` and on PRs (Python 3.14). CI must pass before merging.
- SonarCloud analysis configured in CI.

## Skills

Shared skills from `shared-standards/.claude/skills/` — load `testing-pytest/SKILL.md` when writing tests.
