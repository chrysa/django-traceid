---
name: traceid-propagation-check
description: "Verify trace_id propagates correctly across sync/async Django request paths, streaming responses, and RQ job boundaries before a middleware or context change is considered safe."
when_to_use: "changed middleware.py or context.py, before claiming a middleware fix is safe, before a release, streaming response regression, RQ job losing trace_id"
---

# Trace ID Propagation Check

`django-traceid`'s entire contract: `trace_id` must survive every path a
request or job can take, with zero monkey-patching. This is not generic
API-contract testing — it's specific to this package's sync/async/streaming/RQ
surface.

## Checklist

Walk each row. For each, find or write the test that proves it, then run it.

| Path | What must hold | Where to look |
| --- | --- | --- |
| Sync request (WSGI) | `trace_id` set before view, present in response header | `middleware.py` |
| Async request (ASGI) | Same, across `await` boundaries — no leakage between concurrent coroutines | `middleware.py`, `context.py` |
| Streaming response | `trace_id` still correct on each chunk, not just the first | `middleware.py` |
| RQ job | `trace_id` propagated from enqueue to job execution context | `rq.py` |
| Logging | Filter attaches the request's `trace_id`, not a stale/leaked one | `filters.py` |

## How to verify

1. Run the existing suite scoped to these paths:
   ```bash
   pytest -k "trace_id or async or streaming or rq" --cov=src/django_traceid --cov-report=term-missing
   ```
2. For any row without a passing, specific test, write one before proceeding —
   don't hand-wave "it looks fine."
3. Confirm no `contextvars` leakage: run the async test class with
   `pytest-asyncio` concurrency (multiple simulated requests in the same
   event loop) and assert each sees only its own `trace_id`.
4. Confirm `mypy --strict` still passes on touched files.

## Done means

Every row above has a passing test in this session's run, not just "existing
tests pass" — a regression in one path can hide behind green tests for the
others.
