"""Django application configuration."""

from __future__ import annotations

from django.apps import AppConfig

__all__ = ["TraceIdConfig"]


class TraceIdConfig(AppConfig):
    name = "django_traceid"
    label = "django_traceid"
    verbose_name = "Django Trace ID"
