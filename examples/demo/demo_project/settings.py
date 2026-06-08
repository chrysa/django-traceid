"""Minimal Django settings for the django-traceid demo project.

Three wiring points make every log line carry the same trace id:

1. ``django_traceid`` in ``INSTALLED_APPS``.
2. ``TraceIdMiddleware`` placed as early as possible in ``MIDDLEWARE`` so the
   id is bound before any view or logging happens.
3. ``TraceIdFilter`` attached to the logging config and ``%(trace_id)s``
   referenced in the formatter.
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "demo-insecure-key-not-for-production"  # noqa: S105
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_traceid",
    "orders",
]

MIDDLEWARE = [
    # As early as possible: bind the trace id before anything else runs.
    "django_traceid.middleware.TraceIdMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "demo_project.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

# All keys are optional; shown here to make the demo self-documenting.
TRACEID = {
    "REQUEST_HEADER": "X-Request-ID",
    "RESPONSE_HEADER": "X-Request-ID",
    "LOG_RECORD_ATTR": "trace_id",
    "TRUST_INCOMING_HEADER": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        # Enriches every record with the current trace id (empty outside a request).
        "trace_id": {"()": "django_traceid.filters.TraceIdFilter"},
    },
    "formatters": {
        "with_trace": {
            "format": "[trace=%(trace_id)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["trace_id"],
            "formatter": "with_trace",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
