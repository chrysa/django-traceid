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

__all__ = [
    "__version__",
    "generate_trace_id",
    "get_trace_id",
    "reset_trace_id",
    "set_trace_id",
    "trace_context",
]

try:
    __version__ = version("django-traceid")
except PackageNotFoundError:  # editable install / not installed
    __version__ = "0.0.0+unknown"
