"""Logging filter that enriches every record with the current trace id."""

from __future__ import annotations

import logging

from .conf import traceid_settings
from .context import get_trace_id

__all__ = ["TraceIdFilter"]


class TraceIdFilter(logging.Filter):
    """Attach the current trace id to each record; never drops a record.

    The attribute name is configurable via ``TRACEID["LOG_RECORD_ATTR"]`` and
    defaults to ``trace_id``. Records emitted outside a request context get an
    empty string so formatters referencing the field never raise.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        setattr(record, traceid_settings.LOG_RECORD_ATTR, get_trace_id() or "")
        return True
