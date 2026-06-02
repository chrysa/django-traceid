from __future__ import annotations

from django_traceid import get_trace_id, reset_trace_id, set_trace_id
from django_traceid.rq import (
    TRACE_KWARG,
    enqueue_with_trace,
    restore_trace_context,
    trace_aware,
)


class FakeQueue:
    """Records the enqueue call the way RQ would receive it."""

    def __init__(self):
        self.calls = []

    def enqueue(self, func, *args, **kwargs):
        self.calls.append((func, args, kwargs))
        return "job-id"


def _job(x):  # pragma: no cover - body asserted via wrapper
    return x


def test_enqueue_injects_current_trace_id():
    queue = FakeQueue()
    token = set_trace_id("job-trace")
    enqueue_with_trace(queue, _job, 1)
    reset_trace_id(token)
    _, _, kwargs = queue.calls[0]
    assert kwargs[TRACE_KWARG] == "job-trace"


def test_enqueue_preserves_explicit_trace_id():
    queue = FakeQueue()
    enqueue_with_trace(queue, _job, 1, _trace_id="explicit")
    assert queue.calls[0][2][TRACE_KWARG] == "explicit"


def test_trace_aware_restores_and_strips_kwarg():
    seen = {}

    @trace_aware
    def job(value):
        seen["trace"] = get_trace_id()
        seen["value"] = value

    job(value=7, _trace_id="restored")
    assert seen == {"trace": "restored", "value": 7}
    assert get_trace_id() is None  # restored after the call


def test_trace_aware_without_trace_id_is_passthrough():
    @trace_aware
    def job(value):
        return value * 2

    assert job(value=3) == 6


def test_restore_trace_context_none_returns_none():
    assert restore_trace_context(None) is None
    assert restore_trace_context("") is None


def test_restore_trace_context_binds():
    token = restore_trace_context("redis-trace")
    assert get_trace_id() == "redis-trace"
    reset_trace_id(token)
