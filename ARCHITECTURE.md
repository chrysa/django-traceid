# ARCHITECTURE — django-traceid

> Scope: internal design of the `django_traceid` package. Tags: **FACT** (verified in
> source), **INFERENCE** (reasoned from code), **UNKNOWN** (not determinable from repo).
> Evidence pointers are `path:symbol`.

## 1. Purpose (FACT)

`django-traceid` propagates a single **trace id** (a.k.a. request id) end-to-end through a
Django request: HTTP in → context → logging → response header, and optionally across
background-job / thread boundaries. Every log line emitted while a request is handled carries
the same id, so a full flow is retraceable with one query in Loki/Kibana/Sentry.
Evidence: `README.md`, `src/django_traceid/__init__.py` module docstring.

Design intent (FACT, `README.md` / `CLAUDE.md`): project-agnostic, zero-config, no
monkey-patching, no runtime dependency beyond Django (`rq` is optional and not imported).

## 2. Package layout (FACT)

`src/` layout; the importable package is `django_traceid` (`pyproject.toml`,
`tests/settings.py`). Runtime modules:

| Module | Role | Key symbols |
| --- | --- | --- |
| `context.py` | Per-context storage of the trace id via `contextvars.ContextVar` | `get_trace_id`, `set_trace_id`, `reset_trace_id`, `trace_context` (ctx mgr), `generate_trace_id` |
| `middleware.py` | HTTP middleware: extract/generate id, bind to context, echo on response | `TraceIdMiddleware`, `_tag_sentry` (module-level) |
| `filters.py` | stdlib logging filter injecting the id onto every `LogRecord` | `TraceIdFilter` |
| `conf.py` | Settings surface: merged `TRACEID` dict with defaults + import-string resolution | `traceid_settings`, `DEFAULTS`, `_reload_on_change` |
| `rq.py` | Optional cross-boundary propagation (RQ/Celery/threads), duck-typed | `enqueue_with_trace`, `trace_aware`, `restore_trace_context`, `TRACE_KWARG` |
| `apps.py` | Django `AppConfig` wiring | `TraceIdConfig` |

Public API is re-exported from `__init__.py` (`__all__`), so callers do
`from django_traceid import ...` without knowing internal layout (FACT).

## 3. Core mechanism — the context var (FACT)

`context.py` holds a module-level `ContextVar` for the current trace id. Because it is a
`ContextVar` (not `threading.local`), the value is isolated **per thread and per asyncio
task**, with zero dependency on Django. `set_trace_id` returns a token; `reset_trace_id(token)`
restores the previous value; `trace_context(trace_id)` is a context manager that binds for a
`with` block and restores afterward, treating `None` as a no-op.
`generate_trace_id` returns a UUID v4 as 32 lowercase hex chars (no dashes).

## 4. HTTP flow — `TraceIdMiddleware` (FACT)

Per request (`middleware.py`):
1. Read the incoming id from the configured request header (`REQUEST_HEADER`, default
   `X-Request-ID`) via `request.META`. If `TRUST_INCOMING_HEADER` is true and the raw value
   passes validation, reuse it; otherwise generate a fresh id.
2. Validation of an incoming id: non-empty, length `<= INCOMING_MAX_LENGTH` (default 200), and
   matching the url-safe token pattern `_VALID_INCOMING` (`[A-Za-z0-9_.-]+`, per `middleware.py`).
   This is a **log-injection guard** (INFERENCE from comments + `README.md`).
3. Bind the id to the context, expose it as `request.trace_id`, call the handler, then set the
   `RESPONSE_HEADER` (default `X-Request-ID`) on the response, and reset the context.
4. Optionally tag Sentry (see §7).

**Sync + async** (FACT): the middleware advertises itself as both sync- and async-capable
(`asgiref` `iscoroutinefunction` / `markcoroutinefunction`) and adapts to the wrapped handler,
so it works under WSGI and ASGI.

**Streaming bodies** (FACT): for a sync streaming response the id stays bound until the body is
fully produced — the middleware wraps `streaming_content` in a generator that resets the id only
once the stream is exhausted, so log lines emitted mid-stream still carry it. Async streams are
left to the default reset (their body is iterated within the ASGI task scope).

## 5. Logging integration — `TraceIdFilter` (FACT)

`filters.py`: a `logging.Filter` whose `filter()` sets an attribute (name from
`LOG_RECORD_ATTR`, default `trace_id`) to the current id, or `""` when outside a request
context, and always returns `True` (never drops a record). Formatters can reference the field
(`%(trace_id)s` or a JSON field) without raising. Wiring is done in the host project's
`LOGGING` config (see `README.md`).

## 6. Cross-boundary propagation — `rq.py` (FACT, optional)

A `ContextVar` does not survive a fork/serialize, so the id travels as job metadata:
- `enqueue_with_trace(queue, func, ...)` injects the current id as the `TRACE_KWARG`
  (`_trace_id`) kwarg; an explicit `_trace_id` already in kwargs is preserved.
- `trace_aware` decorator: on the worker, pops `_trace_id` from kwargs (keeping the wrapped
  function's real signature), binds it for the call, then resets.
- `restore_trace_context(trace_id)` binds an id for a manual consumer loop (Redis/MQTT), returns
  the reset token (or `None` when falsy).
- Duck-typed: only requires the queue to expose `enqueue(func, *args, **kwargs)`, so RQ is
  **not imported** — no hard dependency. Celery/threads are supported by the same pattern
  (INFERENCE from docstring, not separately tested here — see TESTING.md).

## 7. Configuration surface — `conf.py` (FACT)

All knobs live under one `TRACEID` dict in host Django settings; every key is optional. See
REQUIREMENTS.md for the full table. `traceid_settings` is a lazy accessor merging `DEFAULTS`
with the host dict, resolving import-string keys (`GENERATOR`) via `import_string`, caching
results, and reloading on the `setting_changed` signal (`_reload_on_change` receiver) — which
makes `override_settings` work in tests (INFERENCE).

Sentry tagging (`SENTRY_TAG`, default per `conf.py DEFAULTS`) is dependency-free: the middleware
imports the host project's own `sentry-sdk` lazily and skips silently if absent; on sentry-sdk
>= 2.0 it tags the per-request isolation scope so the id does not leak across requests sharing a
worker, falling back to the global tag otherwise (FACT, `middleware.py:_tag_sentry`).

## 8. Dependency & portability posture (FACT)

- Runtime deps: Django only (`pyproject.toml`). `rq`, `sentry-sdk` are host-provided/optional.
- No monkey-patching; existing services untouched; enrichment is via a stdlib logging filter.
- Type-checked `mypy --strict`; ships `py.typed` marker (`Typing :: Typed` classifier).

## 9. Known internal inconsistencies (see REVIEW.md)

- README says "5 moving parts, ~90 lines"; CLAUDE.md says "6 moving parts, ~190 statements".
  Actual runtime modules with logic: 6 (`context/middleware/filters/conf/rq/apps`).
