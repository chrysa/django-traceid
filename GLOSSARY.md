# GLOSSARY — django-traceid

- **Trace id / request id** — a single correlation identifier bound to one HTTP request and
  propagated to logs, background jobs and (optionally) Sentry. Default UUID4 as 32 lowercase hex
  chars. Not a secret.
- **`X-Request-ID`** — default HTTP header both read (incoming) and written (response). Configurable
  via `REQUEST_HEADER` / `RESPONSE_HEADER`.
- **`ContextVar`** — `contextvars.ContextVar` storing the current id; isolated per thread and per
  asyncio task. Backs `context.py`.
- **`TraceIdMiddleware`** — Django middleware that extracts/generates the id, binds it, exposes
  `request.trace_id`, and echoes it on the response. Sync- and async-capable.
- **`TraceIdFilter`** — stdlib `logging.Filter` that sets the id (attr `LOG_RECORD_ATTR`, default
  `trace_id`) on every record.
- **`trace_context(id)`** — context manager binding an id for a `with` block; `None` is a no-op.
- **`enqueue_with_trace` / `trace_aware`** — enqueue helper + worker decorator that carry the id
  across a job boundary as the `_trace_id` kwarg (`TRACE_KWARG`).
- **`restore_trace_context(id)`** — bind an id in a manual consumer loop (Redis/MQTT); returns a
  reset token.
- **`TRACEID`** — the single Django settings dict holding all configuration (all keys optional).
- **`SENTRY_TAG`** — opt-in flag to tag the current Sentry scope with the id (uses host sentry-sdk).
- **`TRUST_INCOMING_HEADER`** — when false, the incoming header is never reused; a fresh id is
  always generated.
- **Isolation scope** — sentry-sdk >= 2.0 per-request scope used so the tag does not leak across
  requests on a shared worker.
