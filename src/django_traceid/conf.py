"""Settings access for django-traceid.

All knobs live under a single ``TRACEID`` dict in the host project's Django
settings. Every key is optional and falls back to a sensible default, so the
package works with zero configuration::

    TRACEID = {
        "REQUEST_HEADER": "X-Request-ID",
        "RESPONSE_HEADER": "X-Request-ID",
        "GENERATOR": "django_traceid.context.generate_trace_id",
        "LOG_RECORD_ATTR": "trace_id",
        "TRUST_INCOMING_HEADER": True,
        "INCOMING_MAX_LENGTH": 200,
        "SENTRY_TAG": False,
    }
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.module_loading import import_string

__all__ = ["DEFAULTS", "TraceIdSettings", "traceid_settings"]

DEFAULTS: dict[str, Any] = {
    # HTTP header read on the incoming request to reuse a client-supplied id.
    "REQUEST_HEADER": "X-Request-ID",
    # HTTP header written back on the response.
    "RESPONSE_HEADER": "X-Request-ID",
    # Dotted path to a zero-arg callable returning a new trace id.
    "GENERATOR": "django_traceid.context.generate_trace_id",
    # Attribute name set on each logging.LogRecord by TraceIdFilter.
    "LOG_RECORD_ATTR": "trace_id",
    # Reuse the incoming header value when present (after validation).
    "TRUST_INCOMING_HEADER": True,
    # Reject an incoming header longer than this (log-injection guard).
    "INCOMING_MAX_LENGTH": 200,
    # When sentry_sdk is installed, tag the current scope with the trace id.
    "SENTRY_TAG": False,
}

# Keys whose value is a dotted path that must be imported on access.
_IMPORT_STRINGS = frozenset({"GENERATOR"})


class TraceIdSettings:
    """Lazy, attribute-style access to the merged ``TRACEID`` settings dict."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    @property
    def _user_settings(self) -> dict[str, Any]:
        return getattr(settings, "TRACEID", {}) or {}

    def __getattr__(self, name: str) -> Any:
        if name not in DEFAULTS:
            raise AttributeError(f"Invalid TRACEID setting: {name!r}")
        if name in self._cache:
            return self._cache[name]

        value = self._user_settings.get(name, DEFAULTS[name])
        if name in _IMPORT_STRINGS and isinstance(value, str):
            value = import_string(value)
        self._cache[name] = value
        return value

    @property
    def generator(self) -> Callable[[], str]:
        return cast("Callable[[], str]", self.GENERATOR)

    @property
    def request_meta_key(self) -> str:
        """WSGI/ASGI ``request.META`` key derived from ``REQUEST_HEADER``."""
        header: str = self.REQUEST_HEADER
        return "HTTP_" + header.upper().replace("-", "_")

    def reload(self) -> None:
        self._cache.clear()


traceid_settings = TraceIdSettings()


@receiver(setting_changed)
def _reload_on_change(*, setting: str, **_kwargs: Any) -> None:
    if setting == "TRACEID":
        traceid_settings.reload()
