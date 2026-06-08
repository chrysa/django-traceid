"""URL configuration for the demo project."""

from __future__ import annotations

from django.urls import path

from orders import views

urlpatterns = [
    path("", views.index, name="index"),
    path("orders/<int:order_id>/", views.process_order, name="process-order"),
]
