# OBSERVABILITY — django-traceid

This library *is* an observability tool: it exists to make logs and traces correlatable. This
doc records what it emits and how it plugs into a stack.

## What it produces (FACT)

- **A trace id per request**, exposed as `request.trace_id` and echoed on the response header
  (`RESPONSE_HEADER`, default `X-Request-ID`). Evidence: `middleware.py`.
- **A `trace_id` field on every log record** (attribute name from `LOG_RECORD_ATTR`), via
  `TraceIdFilter`. Records outside a request get `""`. Evidence: `filters.py`.

## Wiring into a logging stack (FACT — `README.md`)

Add `TraceIdMiddleware` to `MIDDLEWARE`, add `TraceIdFilter` to the `filters` of your Django
`LOGGING` config, attach the filter to the handlers, and reference the field in the formatter
(`%(trace_id)s` for a plain formatter, or the field directly in a JSON formatter). No formatter
raises when the field is absent because the filter always sets it.

Intended sinks: Loki, Kibana, Sentry — "retraceable with one query" (README/CLAUDE.md).

## Sentry integration (FACT)

Opt-in via `TRACEID["SENTRY_TAG"] = True`. The middleware tags the current Sentry scope with the
id using the **host project's** `sentry-sdk` (lazy import, silently skipped if absent). On
sentry-sdk >= 2.0 it tags the per-request isolation scope to avoid cross-request bleed; older
versions fall back to a global tag. Evidence: `middleware.py:_tag_sentry`, `README.md`.

## Cross-boundary correlation (FACT)

The same id can be carried into background jobs and manual consumer loops so downstream log lines
share it (`rq.py`; see ARCHITECTURE.md §6). This closes the HTTP → jobs → pub/sub loop.

## Not provided (INFERENCE / scope note)

- No metrics, no OpenTelemetry span emission, no distributed-trace propagation headers beyond the
  single request-id header. It is a **correlation id**, not a full tracing SDK. UNKNOWN whether
  W3C `traceparent` interop is planned (not present in code).
