# Architecture — django-traceid

## Purpose

End-to-end request/trace id propagation for Django. Every log line emitted while
handling a request carries the same `trace_id`, so a full flow (HTTP → services →
ORM → background jobs → pub/sub) can be retraced with a single query in Loki,
Kibana or Sentry. The package is project-agnostic and zero-config: it touches no
existing service and does no monkey-patching. Async- and thread-safe via
`contextvars.ContextVar` (not `threading.local`).

## Stack

- **Language:** Python 3.12+ (hard floor — uses PEP 695 generic syntax; tested on 3.14).
- **Framework:** Django 4.2+ (new-style middleware, `import_string`, the
  `setting_changed` signal, `AppConfig`).
- **Runtime dependency:** `Django>=4.2` only (see `pyproject.toml`).
- **Dev tooling:** pytest, pytest-django, pytest-cov, ruff, mypy, django-stubs.
- **Packaging:** `pyproject.toml` (src layout), ships `py.typed` (typed package).

## Layout

- `src/django_traceid/` — the package (src layout):
  - `__init__.py` — public API re-exports and `__version__` (from installed metadata).
  - `context.py` — `ContextVar`-backed trace id storage: `get_trace_id`,
    `set_trace_id`, `reset_trace_id`, `trace_context`, `generate_trace_id`.
  - `middleware.py` — `TraceIdMiddleware` (reads/sets request/response headers).
  - `filters.py` — `TraceIdFilter` logging filter (injects `trace_id` into records).
  - `conf.py` — settings access with defaults (`REQUEST_HEADER`/`RESPONSE_HEADER`
    = `X-Request-ID`, `GENERATOR` = `django_traceid.context.generate_trace_id`,
    plus a `SENTRY_TAG` option) reloaded on the `setting_changed` signal.
  - `apps.py` — Django `AppConfig`.
  - `rq.py` — background-job propagation: `TRACE_KWARG`, `enqueue_with_trace`,
    `restore_trace_context`, `trace_aware`.
- `tests/` — pytest suite (settings, urls, and tests incl. `test_rq.py`).
- `examples/demo/` — minimal Django demo project.
- `docs/`, `standards/`, `legal/`, `scripts/` — supporting material.
- Root: `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`,
  `Makefile`, `Dockerfile.test`, `Dockerfile.typecheck`, `pyproject.toml`,
  `.pre-commit-config.yaml`, `cliff.toml`, `GitVersion.yml`.

## Entrypoints

This is a library, not an application. Integration points:

- **Public API:** `from django_traceid import ...` — `TraceIdMiddleware`,
  `TraceIdFilter`, `get_trace_id`/`set_trace_id`/`reset_trace_id`/`trace_context`,
  `generate_trace_id`, and the RQ helpers (`enqueue_with_trace`,
  `restore_trace_context`, `trace_aware`, `TRACE_KWARG`).
- **Middleware:** add `TraceIdMiddleware` to Django `MIDDLEWARE`.
- **Logging:** wire `TraceIdFilter` into `LOGGING` and reference `%(trace_id)s`
  (plain formatter) or the field directly (JSON).

## Data / external deps

- No database, no persistence: the trace id lives only in a request-scoped
  `ContextVar`.
- **HTTP headers:** reads incoming `REQUEST_HEADER` (default `X-Request-ID`) and
  sets outgoing `RESPONSE_HEADER` (default `X-Request-ID`); reuses the incoming id
  when present, otherwise generates one via the configured `GENERATOR`.
- **Optional Sentry:** when `SENTRY_TAG` is enabled and `sentry_sdk` is present in
  the host project, tags the current Sentry scope (soft/optional integration).
- **Optional RQ / background jobs:** helpers in `rq.py` carry the trace id across
  enqueue/execute boundaries.

## Build & test

Real commands (from `Makefile` / `pyproject.toml`):

```bash
make install       # pip install -e ".[dev]"
make test          # pytest (coverage: --cov-fail-under=85)
make test-cov      # tests with coverage
make lint          # ruff
make format        # ruff auto-format
make typecheck     # mypy in Docker (Dockerfile.typecheck)
make docker-test   # tests in Docker (Dockerfile.test), CI-compatible
make pre-commit    # pre-commit run --all-files
make ci            # lint + typecheck + test
```
