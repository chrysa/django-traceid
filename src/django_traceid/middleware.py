"""HTTP middleware binding a trace id to each request."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, cast

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from .conf import traceid_settings
from .context import reset_trace_id, set_trace_id

if TYPE_CHECKING:
    import contextvars

    from django.http import HttpRequest, HttpResponse

__all__ = ["TraceIdMiddleware"]

# A trusted incoming id may only contain url-safe token characters.
_VALID_INCOMING = re.compile(r"\A[A-Za-z0-9_.\-]+\Z")


class TraceIdMiddleware:
    """Bind a trace id for the lifetime of each request.

    The id is taken from the configured request header when present and valid,
    otherwise a new one is generated. It is exposed as ``request.trace_id`` and
    echoed back in the response header.

    Works under both WSGI and ASGI: the middleware advertises itself as
    sync- *and* async-capable and adapts to the wrapped handler. For a streaming
    response the trace id stays bound until the body is fully produced, so log
    lines emitted while streaming still carry the id.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._meta_key = traceid_settings.request_meta_key
        self._response_header = traceid_settings.RESPONSE_HEADER
        self._trust_incoming = traceid_settings.TRUST_INCOMING_HEADER
        self._max_len = traceid_settings.INCOMING_MAX_LENGTH
        self._generate = traceid_settings.generator
        self._sentry_tag = traceid_settings.SENTRY_TAG
        self._is_async = iscoroutinefunction(get_response)
        if self._is_async:
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> Any:
        if self._is_async:
            return self.__acall__(request)
        trace_id, token = self._bind(request)
        try:
            response = self.get_response(request)
        except BaseException:
            reset_trace_id(token)
            raise
        return self._finalize(response, trace_id, token)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        trace_id, token = self._bind(request)
        try:
            response = await cast("Any", self.get_response)(request)
        except BaseException:
            reset_trace_id(token)
            raise
        return self._finalize(response, trace_id, token)

    def _bind(self, request: HttpRequest) -> tuple[str, contextvars.Token[str | None]]:
        trace_id = self._incoming(request) or self._generate()
        cast(Any, request).trace_id = trace_id
        token = set_trace_id(trace_id)
        if self._sentry_tag:
            _tag_sentry(trace_id)
        return trace_id, token

    def _finalize(
        self,
        response: HttpResponse,
        trace_id: str,
        token: contextvars.Token[str | None],
    ) -> HttpResponse:
        response[self._response_header] = trace_id
        # A streaming body is produced lazily, *after* this middleware returns.
        # Keep the id bound and reset only once the stream is exhausted, so log
        # lines emitted mid-stream still carry it. Async streams are left to the
        # default reset (their body is iterated within the ASGI task scope).
        if getattr(response, "streaming", False) and not getattr(response, "is_async", False):
            response.streaming_content = _reset_after(  # type: ignore[attr-defined]
                cast("Iterator[bytes]", response.streaming_content),  # type: ignore[attr-defined]
                token,
            )
            return response
        reset_trace_id(token)
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


def _reset_after(
    content: Iterator[bytes],
    token: contextvars.Token[str | None],
) -> Iterator[bytes]:
    """Yield ``content`` unchanged, then reset the trace id once exhausted."""
    try:
        yield from content
    finally:
        reset_trace_id(token)


def _tag_sentry(trace_id: str) -> None:
    try:
        import sentry_sdk
    except ImportError:
        return
    # Tag the per-request isolation scope (sentry-sdk >= 2.0) so the id does not
    # leak into other requests sharing the worker; fall back to the global tag on
    # older SDKs.
    get_isolation_scope = getattr(sentry_sdk, "get_isolation_scope", None)
    if get_isolation_scope is not None:
        get_isolation_scope().set_tag("trace_id", trace_id)
    else:
        sentry_sdk.set_tag("trace_id", trace_id)
