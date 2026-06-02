"""Execution-context storage for the trace id.

Backed by :class:`contextvars.ContextVar` so the value is isolated per thread
*and* per asyncio task, with zero dependency on Django itself.
"""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

__all__ = [
    "generate_trace_id",
    "get_trace_id",
    "reset_trace_id",
    "set_trace_id",
    "trace_context",
]

_trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("django_traceid.trace_id", default=None)


def get_trace_id() -> str | None:
    """Return the trace id bound to the current context, or ``None``."""
    return _trace_id_var.get()


def set_trace_id(trace_id: str) -> contextvars.Token[str | None]:
    """Bind ``trace_id`` to the current context.

    Returns the token required to restore the previous value with
    :func:`reset_trace_id`.
    """
    return _trace_id_var.set(trace_id)


def reset_trace_id(token: contextvars.Token[str | None]) -> None:
    """Restore the value the context held before the matching :func:`set_trace_id`."""
    _trace_id_var.reset(token)


def generate_trace_id() -> str:
    """Return a fresh UUID v4 as 32 lowercase hex characters (no dashes)."""
    return uuid.uuid4().hex


@contextmanager
def trace_context(trace_id: str | None) -> Iterator[str | None]:
    """Bind ``trace_id`` for the duration of the ``with`` block, then restore.

    Passing ``None`` is a no-op (the current value is left untouched), which makes
    it safe to wrap a worker/consumer regardless of whether a trace id was
    propagated.
    """
    if trace_id is None:
        yield get_trace_id()
        return
    token = set_trace_id(trace_id)
    try:
        yield trace_id
    finally:
        reset_trace_id(token)
