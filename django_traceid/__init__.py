"""django-traceid — end-to-end request/trace id propagation for Django.

Public API re-exported here so callers can ``from django_traceid import ...``
without knowing the internal module layout.
"""

from __future__ import annotations

from .context import (
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
    trace_context,
)

__all__ = [
    "__version__",
    "generate_trace_id",
    "get_trace_id",
    "reset_trace_id",
    "set_trace_id",
    "trace_context",
]

__version__ = "0.1.0"
