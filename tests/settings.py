"""Minimal Django settings to exercise django-traceid under pytest."""

from __future__ import annotations

import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "test-only-not-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_traceid",
]

MIDDLEWARE = [
    "django_traceid.middleware.TraceIdMiddleware",
]

ROOT_URLCONF = "tests.urls"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
