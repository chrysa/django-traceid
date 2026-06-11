"""Trace-id propagation across process boundaries (RQ, Celery, threads...).

A ``contextvars.ContextVar`` does not survive a fork/serialize, so the id must
travel as job metadata. These helpers are duck-typed: ``enqueue_with_trace``
only requires ``queue`` to expose an ``enqueue(func, *args, **kwargs)`` method,
so they work with RQ without importing it (no hard dependency).

Usage::

    from django_traceid.rq import enqueue_with_trace, trace_aware

    @trace_aware
    def process_mission(mission_id): ...

    enqueue_with_trace(queue, process_mission, mission_id)
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, Protocol, cast

from .context import get_trace_id, reset_trace_id, set_trace_id

__all__ = ["TRACE_KWARG", "enqueue_with_trace", "restore_trace_context", "trace_aware"]

#: Keyword used to smuggle the trace id through the job payload.
TRACE_KWARG = "_trace_id"


class SupportsEnqueue(Protocol):
    """Minimal queue interface required by :func:`enqueue_with_trace`.

    Captures the single method the helper depends on, so any RQ-like queue is
    accepted without importing RQ (no hard dependency).
    """

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any: ...


def enqueue_with_trace(queue: SupportsEnqueue, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Enqueue ``func`` on ``queue`` carrying the current trace id.

    The id is injected as the ``_trace_id`` kwarg; pair this with the
    :func:`trace_aware` decorator on ``func`` so the worker restores and strips
    it automatically. An explicit ``_trace_id`` in ``kwargs`` is preserved.
    """
    kwargs.setdefault(TRACE_KWARG, get_trace_id())
    return queue.enqueue(func, *args, **kwargs)


def trace_aware[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Restore the propagated trace id for the duration of the call.

    Pops ``_trace_id`` from kwargs (so the wrapped function keeps its real
    signature), binds it to the context, then resets it afterwards.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        trace_id = cast("str | None", kwargs.pop(TRACE_KWARG, None))
        if trace_id is None:
            return func(*args, **kwargs)
        token = set_trace_id(trace_id)
        try:
            return func(*args, **kwargs)
        finally:
            reset_trace_id(token)

    return wrapper


def restore_trace_context(trace_id: str | None) -> Any:
    """Bind ``trace_id`` to the context for manual consumer loops (Redis, MQTT).

    Returns the token to pass to :func:`django_traceid.context.reset_trace_id`,
    or ``None`` when ``trace_id`` is falsy (nothing to restore).
    """
    if not trace_id:
        return None
    return set_trace_id(trace_id)
