# django-traceid

End-to-end **trace / request id** propagation for Django — project-agnostic,
zero-config, no monkey-patching. Every log line emitted while handling a request
carries the same `trace_id`, so you can retrace a full flow (HTTP → services →
ORM → background jobs → pub/sub) with a single query in Loki, Kibana or Sentry.

- **5 moving parts, ~90 lines** of runtime code. No existing service is touched.
- **Automatic log enrichment** via a stdlib logging filter — existing
  `logger.info(...)` calls get `trace_id` for free, all formatters included.
- **Async- and thread-safe** through `contextvars.ContextVar` (no `threading.local`).
- **Cross-process propagation** helpers for RQ / Celery / Redis pub/sub / MQTT.

## Compatibility

| | Supported | Notes |
|---|---|---|
| **Python** | **3.12+** | Hard floor: the package uses PEP 695 generic syntax (`def trace_aware[F: ...]`), which does not parse before 3.12. Tested on 3.14. |
| **Django** | **4.2+** | Only stable, long-standing APIs are used (new-style middleware, `import_string`, the `setting_changed` signal, `AppConfig`), so it runs on much older Django too; 4.2 LTS is the supported floor. |

## Install

```bash
pip install django-traceid
```

> **Sentry tagging is optional and dependency-free.** django-traceid never
> bundles `sentry-sdk`. In a project that already uses Sentry, just set
> `TRACEID["SENTRY_TAG"] = True`; the middleware tags the current scope using
> the host project's own `sentry-sdk` (imported lazily, silently skipped if
> absent). Nothing to install here.

## Setup (HTTP — Phase 1)

```python
# settings.py
INSTALLED_APPS = [..., "django_traceid"]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django_traceid.middleware.TraceIdMiddleware",  # as early as possible
    ...,
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "trace_id": {"()": "django_traceid.filters.TraceIdFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["trace_id"],
            "formatter": "json",
        },
    },
    "formatters": {
        # reference %(trace_id)s in a plain formatter, or the field directly in JSON
        "json": {"format": '{"level":"%(levelname)s","msg":"%(message)s","trace_id":"%(trace_id)s"}'},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

That's it. Requests now carry `X-Request-ID` (reused from the client if present
and valid, generated otherwise) and every log line gets `trace_id`.

## Configuration

All optional, under a single `TRACEID` dict:

```python
TRACEID = {
    "REQUEST_HEADER": "X-Request-ID",       # incoming header to reuse
    "RESPONSE_HEADER": "X-Request-ID",      # outgoing header to set
    "GENERATOR": "django_traceid.context.generate_trace_id",  # dotted path
    "LOG_RECORD_ATTR": "trace_id",          # LogRecord attribute name
    "TRUST_INCOMING_HEADER": True,          # reuse client-supplied id
    "INCOMING_MAX_LENGTH": 200,             # reject longer (log-injection guard)
    "SENTRY_TAG": False,                    # tag host project's sentry_sdk scope (if present)
}
```

Incoming ids are validated against `[A-Za-z0-9_.-]+` and the max length; anything
else is discarded and a fresh id is generated, so an attacker can't inject
arbitrary content into your logs.

## Background jobs (Phase 2 — RQ / Celery)

A `ContextVar` does not survive a fork, so the id travels as job metadata:

```python
from django_traceid.rq import enqueue_with_trace, trace_aware

@trace_aware                      # restores the id on the worker, strips the kwarg
def process_mission(mission_id):
    ...

enqueue_with_trace(queue, process_mission, mission_id)  # captures current id
```

`enqueue_with_trace` is duck-typed (`queue.enqueue(...)`) — it works with RQ
without importing it, so RQ is not a dependency.

## Manual consumers (Phase 3 — Redis pub/sub, MQTT)

Put `get_trace_id()` in the published payload, restore it on the consumer:

```python
from django_traceid import get_trace_id, reset_trace_id
from django_traceid.rq import restore_trace_context

# producer
payload = {"trace_id": get_trace_id(), "vehicle_id": 42, ...}

# consumer
token = restore_trace_context(data.get("trace_id"))
try:
    handle(data)        # logs carry the original trace_id
finally:
    reset_trace_id(token)
```

Or the context-manager form for any worker loop:

```python
from django_traceid import trace_context

with trace_context(data.get("trace_id")):
    handle(data)
```

## LogQL example (Grafana / Loki)

`trace_id` should be a JSON **field**, never a Loki label (infinite cardinality):

```logql
{app="my-service"} | json | trace_id="550e8400e29b41d4a716446655440000"
```

## Public API

| Import | Purpose |
|---|---|
| `get_trace_id()` | current id or `None` |
| `set_trace_id(id)` → token | bind, returns reset token |
| `reset_trace_id(token)` | restore previous value |
| `generate_trace_id()` | new uuid4 hex (32 chars) |
| `trace_context(id)` | context manager (bind + auto-reset) |
| `django_traceid.rq.enqueue_with_trace` | enqueue carrying the id |
| `django_traceid.rq.trace_aware` | worker-side decorator |
| `django_traceid.rq.restore_trace_context` | bind for manual loops |

## License

MIT
