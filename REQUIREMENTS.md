# REQUIREMENTS — django-traceid

> Derived from source and README. Status is **IMPLEMENTED** only where verifiable in code
> (evidence pointer given) and, where noted, covered by a test. Tags: FACT / INFERENCE.

## Functional requirements

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| REQ-HTTP-001 | Bind a trace id to every request for its lifetime, exposed as `request.trace_id` | IMPLEMENTED | `middleware.py:TraceIdMiddleware.__call__` |
| REQ-HTTP-002 | Reuse a valid client-supplied id from the configured request header | IMPLEMENTED | `middleware.py:_incoming`; `tests/test_middleware.py` |
| REQ-HTTP-003 | Generate a fresh id (UUID4 hex, 32 chars) when none is supplied/valid | IMPLEMENTED | `context.py:generate_trace_id`; middleware fallback |
| REQ-HTTP-004 | Echo the id back on the response via the configured response header | IMPLEMENTED | `middleware.py:TraceIdMiddleware.__call__` |
| REQ-HTTP-005 | Work under both WSGI (sync) and ASGI (async) handlers | IMPLEMENTED | `middleware.py` (`iscoroutinefunction`/`markcoroutinefunction`) |
| REQ-HTTP-006 | Keep the id bound through a sync streaming response until body exhausted | IMPLEMENTED | `middleware.py` streaming-content wrapper generator |
| REQ-LOG-001 | Inject the current id onto every `LogRecord` under a configurable attribute | IMPLEMENTED | `filters.py:TraceIdFilter.filter`; `tests/test_filters.py` |
| REQ-LOG-002 | Emit empty string (never drop record) when outside a request context | IMPLEMENTED | `filters.py` returns `True`, `get_trace_id() or ""` |
| REQ-CTX-001 | Store id per thread AND per asyncio task | IMPLEMENTED | `context.py` `ContextVar` |
| REQ-CTX-002 | Provide bind/reset + a `with` context manager (`None` = no-op) | IMPLEMENTED | `context.py:set_trace_id/reset_trace_id/trace_context` |
| REQ-JOB-001 | Propagate id into a background job via metadata kwarg | IMPLEMENTED | `rq.py:enqueue_with_trace` (`TRACE_KWARG`) |
| REQ-JOB-002 | Restore + strip the id on the worker automatically | IMPLEMENTED | `rq.py:trace_aware` |
| REQ-JOB-003 | Support any RQ-like queue without importing RQ (duck-typed) | IMPLEMENTED | `rq.py` `_Enqueueable` protocol; no `import rq` |
| REQ-JOB-004 | Restore id for manual consumer loops (Redis/MQTT) | IMPLEMENTED | `rq.py:restore_trace_context` |
| REQ-OBS-001 | Optionally tag Sentry scope with the id, no bundled dependency | IMPLEMENTED | `middleware.py:_tag_sentry` (lazy import, isolation scope) |

## Security requirements

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| REQ-SEC-001 | Validate incoming id against a url-safe charset before reuse | IMPLEMENTED | `middleware.py:_VALID_INCOMING` (`[A-Za-z0-9_.-]+`) |
| REQ-SEC-002 | Reject over-length incoming ids (log-injection / DoS guard) | IMPLEMENTED | `middleware.py` `len(raw) > _max_len`; default `INCOMING_MAX_LENGTH=200` |
| REQ-SEC-003 | Allow disabling reuse of the incoming header entirely | IMPLEMENTED | `TRUST_INCOMING_HEADER` toggle, `conf.py DEFAULTS` |

## Configuration surface (`TRACEID` dict) (FACT — `conf.py DEFAULTS`, `README.md`)

| Key | Default | Meaning |
| --- | --- | --- |
| `REQUEST_HEADER` | `X-Request-ID` | Incoming header read to reuse a client id |
| `RESPONSE_HEADER` | `X-Request-ID` | Header written back on the response |
| `GENERATOR` | `django_traceid.context.generate_trace_id` | Dotted path to a zero-arg id generator |
| `LOG_RECORD_ATTR` | `trace_id` | Attribute name set on each `LogRecord` |
| `TRUST_INCOMING_HEADER` | `True` | Reuse the (validated) incoming id when present |
| `INCOMING_MAX_LENGTH` | `200` | Reject an incoming id longer than this |
| `SENTRY_TAG` | (see `conf.py DEFAULTS`) | Tag the current Sentry scope with the id when sentry-sdk present |

## Non-functional / compatibility (FACT — `pyproject.toml`, `README.md`)

- Python **3.12+** (hard floor: PEP 695 generic syntax in `rq.py trace_aware`). CI tests 3.14.
- Django **4.2+** (LTS floor; only long-standing APIs used).
- Zero runtime dependency beyond Django; `rq`/`sentry-sdk` optional and host-provided.
- `mypy --strict` clean; typed distribution (`py.typed`).
- Coverage gate `--cov-fail-under=85` (`pyproject.toml`).
