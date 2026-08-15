"""django-traceid — end-to-end request/trace id propagation for Django.

Public API re-exported here so callers can ``from django_traceid import ...``
without knowing the internal module layout.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .context import (
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
    trace_context,
)
from .filters import TraceIdFilter
from .middleware import TraceIdMiddleware
from .rq import (
    TRACE_KWARG,
    enqueue_with_trace,
    restore_trace_context,
    trace_aware,
)

__all__ = [
    "TRACE_KWARG",
    "TraceIdFilter",
    "TraceIdMiddleware",
    "__version__",
    "enqueue_with_trace",
    "generate_trace_id",
    "get_trace_id",
    "reset_trace_id",
    "restore_trace_context",
    "set_trace_id",
    "trace_aware",
    "trace_context",
]

try:
    __version__ = version("django-traceid")
except PackageNotFoundError:  # editable install / not installed
    __version__ = "0.0.0+unknown"
