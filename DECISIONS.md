# DECISIONS — django-traceid

Architecture decisions inferred from the code and stated rationale. These are reconstructions
(the repo ships no `docs/adr/` records — `handover.md` lists ADRs as "not available"), tagged
INFERENCE unless a source states the rationale explicitly (FACT).

## ADR-001 — Store the trace id in a `contextvars.ContextVar`, not `threading.local`
- **Decision (FACT).** The current id lives in a module-level `ContextVar` (`context.py`).
- **Why (FACT, docstring).** A `ContextVar` isolates the value per thread *and* per asyncio
  task, so the library is correct under both WSGI and ASGI with no Django dependency.
- **Consequence.** The value does not survive fork/serialize → motivates ADR-004.

## ADR-002 — Zero hard dependency beyond Django; optional integrations imported lazily
- **Decision (FACT).** Runtime deps = Django only (`pyproject.toml`). `rq` and `sentry-sdk` are
  never imported at module top level; RQ support is duck-typed and Sentry is imported lazily.
- **Why (FACT, README/docstrings).** Keep the package project-agnostic and installable anywhere
  without pulling a queue or an error tracker.

## ADR-003 — No monkey-patching; enrich logging via a stdlib `logging.Filter`
- **Decision (FACT).** `TraceIdFilter` attaches the id to every `LogRecord`; wiring is host
  `LOGGING` config. No existing service or logger is patched.
- **Why (INFERENCE).** Least-surprise, framework-native integration; existing `logger.info(...)`
  calls gain the field for free.

## ADR-004 — Propagate across process boundaries as job metadata (a kwarg), duck-typed
- **Decision (FACT).** `enqueue_with_trace` smuggles the id as the `_trace_id` kwarg;
  `trace_aware` restores/strips it on the worker. Only `queue.enqueue(...)` is required.
- **Why (FACT, docstring).** A `ContextVar` cannot cross a fork; metadata travels with the job.
  Duck-typing avoids a hard RQ dependency and also serves Celery/threads.

## ADR-005 — Treat the incoming id header as hostile: validate + length-cap before reuse
- **Decision (FACT).** Reuse only ids matching `[A-Za-z0-9_.-]+` and within `INCOMING_MAX_LENGTH`;
  otherwise generate. Reuse can be disabled via `TRUST_INCOMING_HEADER`.
- **Why (FACT/INFERENCE).** Log-injection and unbounded-length guard (see SECURITY.md).

## ADR-006 — Single `TRACEID` settings dict with lazy accessor and live reload
- **Decision (FACT).** All knobs under one optional `TRACEID` dict; `traceid_settings` merges
  defaults, resolves import-strings, caches, and reloads on `setting_changed`.
- **Why (INFERENCE).** Zero-config default; `override_settings` works cleanly in tests.

## ADR-007 — Tag the Sentry isolation scope (sentry-sdk >= 2.0), fall back to global tag
- **Decision (FACT).** `_tag_sentry` prefers the per-request isolation scope so the id does not
  leak across requests sharing a worker; falls back to `sentry_sdk.set_tag` otherwise.
- **Why (FACT, comment).** Prevent cross-request tag bleed on modern sentry-sdk.
