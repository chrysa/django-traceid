"""Demo views that emit a few log lines per request.

Every record produced while handling a request carries the same ``trace_id``
(see the ``with_trace`` formatter in settings), and the response echoes the id
in the ``X-Request-ID`` header — so a single id ties the logs to the response.
"""

from __future__ import annotations

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger("orders")


def index(request: HttpRequest) -> HttpResponse:
    """Landing page with a pointer to the order endpoint."""
    logger.info("index page served")
    return HttpResponse(
        "<h1>django-traceid demo</h1>"
        '<p>Hit <a href="/orders/42/">/orders/42/</a> and watch the server log: '
        "every line for that request shares one trace id, echoed in the "
        "<code>X-Request-ID</code> response header.</p>"
    )


def process_order(request: HttpRequest, order_id: int) -> JsonResponse:
    """Pretend to process an order, logging at several steps.

    The three log lines below all share the request's trace id without any
    code here passing it around — the filter reads it from the context var.
    """
    logger.info("received order %s", order_id)
    logger.info("charging payment for order %s", order_id)
    logger.info("order %s confirmed", order_id)
    return JsonResponse({"order_id": order_id, "status": "confirmed"})
