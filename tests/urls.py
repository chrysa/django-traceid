"""URLConf for the middleware tests."""

from __future__ import annotations

import logging

from django.http import HttpResponse
from django.urls import path

from django_traceid import get_trace_id

logger = logging.getLogger("tests")


def echo(request):
    """Return the trace id seen inside the view (proves the ContextVar is bound)."""
    logger.info("inside view")
    return HttpResponse(get_trace_id() or "")


urlpatterns = [path("echo/", echo)]
