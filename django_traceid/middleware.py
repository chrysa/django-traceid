"""HTTP middleware binding a trace id to each request."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .conf import traceid_settings
from .context import reset_trace_id, set_trace_id

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

__all__ = ["TraceIdMiddleware"]

# A trusted incoming id may only contain url-safe token characters.
_VALID_INCOMING = re.compile(r"\A[A-Za-z0-9_.\-]+\Z")


class TraceIdMiddleware:
    """Bind a trace id for the lifetime of each request.

    The id is taken from the configured request header when present and valid,
    otherwise a new one is generated. It is exposed as ``request.trace_id`` and
    echoed back in the response header.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._meta_key = traceid_settings.request_meta_key
        self._response_header = traceid_settings.RESPONSE_HEADER
        self._trust_incoming = traceid_settings.TRUST_INCOMING_HEADER
        self._max_len = traceid_settings.INCOMING_MAX_LENGTH
        self._generate = traceid_settings.generator
        self._sentry_tag = traceid_settings.SENTRY_TAG

    def __call__(self, request: HttpRequest) -> HttpResponse:
        trace_id = self._incoming(request) or self._generate()
        cast(Any, request).trace_id = trace_id
        token = set_trace_id(trace_id)
        if self._sentry_tag:
            _tag_sentry(trace_id)
        try:
            response = self.get_response(request)
        finally:
            reset_trace_id(token)
        response[self._response_header] = trace_id
        return response

    def _incoming(self, request: HttpRequest) -> str | None:
        if not self._trust_incoming:
            return None
        raw: str | None = request.META.get(self._meta_key)
        if not raw:
            return None
        raw = raw.strip()
        if not raw or len(raw) > self._max_len or not _VALID_INCOMING.match(raw):
            return None
        return raw


def _tag_sentry(trace_id: str) -> None:
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.set_tag("trace_id", trace_id)
