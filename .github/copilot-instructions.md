# django-traceid — GitHub Copilot Instructions

## Purpose

End-to-end trace/request ID propagation for Django without monkey-patching.
Injects a `trace_id` into every HTTP request and log record so a single query
in Loki/Kibana/Sentry follows a flow across services, ORM, and background jobs.

## Conventions

- Python ≥3.12 (uses PEP 695 generic syntax), Django ≥4.2. Flat layout (`django_traceid/`).
- Core: `contextvars.ContextVar` (async/thread-safe), HTTP middleware, stdlib logging filter.
- ruff, mypy strict, coverage `fail_under = 85`.
- All tests/lint/build go through Docker or pre-commit — never on host.

## Commands

`make test` · `make lint` · `make typecheck` · `make docker-test`
