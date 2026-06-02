from __future__ import annotations

import logging

from django.test import override_settings

from django_traceid import reset_trace_id, set_trace_id
from django_traceid.filters import TraceIdFilter


def _record():
    return logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)


def test_filter_injects_trace_id():
    token = set_trace_id("trace-xyz")
    record = _record()
    assert TraceIdFilter().filter(record) is True
    assert record.trace_id == "trace-xyz"
    reset_trace_id(token)


def test_filter_empty_string_outside_context():
    record = _record()
    TraceIdFilter().filter(record)
    assert record.trace_id == ""


@override_settings(TRACEID={"LOG_RECORD_ATTR": "request_id"})
def test_filter_respects_custom_attr():
    token = set_trace_id("rid-1")
    record = _record()
    TraceIdFilter().filter(record)
    assert record.request_id == "rid-1"
    reset_trace_id(token)
