from __future__ import annotations

import re

from django_traceid import (
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
    trace_context,
)


def test_generate_trace_id_is_32_hex():
    tid = generate_trace_id()
    assert re.fullmatch(r"[0-9a-f]{32}", tid)
    assert generate_trace_id() != tid


def test_default_is_none():
    assert get_trace_id() is None


def test_set_and_reset_round_trips():
    token = set_trace_id("abc-123")
    assert get_trace_id() == "abc-123"
    reset_trace_id(token)
    assert get_trace_id() is None


def test_set_is_nestable():
    outer = set_trace_id("outer")
    inner = set_trace_id("inner")
    assert get_trace_id() == "inner"
    reset_trace_id(inner)
    assert get_trace_id() == "outer"
    reset_trace_id(outer)


def test_trace_context_binds_and_restores():
    with trace_context("ctx-1") as tid:
        assert tid == "ctx-1"
        assert get_trace_id() == "ctx-1"
    assert get_trace_id() is None


def test_trace_context_none_is_noop():
    token = set_trace_id("keep")
    with trace_context(None) as tid:
        assert tid == "keep"
        assert get_trace_id() == "keep"
    assert get_trace_id() == "keep"
    reset_trace_id(token)
