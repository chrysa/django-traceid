"""AppConfig for the demo orders app."""

from __future__ import annotations

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Configuration for the demo orders app."""

    default_auto_field = "django.db.models.AutoField"
    name = "orders"
