"""URLConf for the middleware tests."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from django.http import HttpResponse, StreamingHttpResponse
from django.urls import path

from django_traceid import get_trace_id

logger = logging.getLogger("tests")


def echo(request):
    """Return the trace id seen inside the view (proves the ContextVar is bound)."""
    logger.info("inside view")
    return HttpResponse(get_trace_id() or "")


def stream(request):
    """Stream the trace id read *inside* the generator, i.e. after the middleware returns.

    Proves the id stays bound for the whole streamed body, not only until the
    middleware's ``__call__`` returns.
    """

    def body() -> Iterator[bytes]:
        logger.info("inside stream")
        yield (get_trace_id() or "").encode()

    return StreamingHttpResponse(body())


async def aecho(request):
    """Async view: return the trace id bound in the ASGI task context."""
    return HttpResponse(get_trace_id() or "")


urlpatterns = [
    path("echo/", echo),
    path("stream/", stream),
    path("aecho/", aecho),
]
