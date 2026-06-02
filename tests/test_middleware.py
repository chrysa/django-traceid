from __future__ import annotations

import re

import pytest
from django.test import Client, override_settings

from django_traceid import get_trace_id


@pytest.fixture
def client():
    return Client()


def test_generates_id_when_header_absent(client):
    resp = client.get("/echo/")
    assert resp.status_code == 200
    rid = resp["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f]{32}", rid)
    # The view saw the same id the response echoes.
    assert resp.content.decode() == rid


def test_reuses_valid_incoming_header(client):
    resp = client.get("/echo/", HTTP_X_REQUEST_ID="client-supplied-42")
    assert resp["X-Request-ID"] == "client-supplied-42"
    assert resp.content.decode() == "client-supplied-42"


def test_rejects_injection_in_incoming_header(client):
    resp = client.get("/echo/", HTTP_X_REQUEST_ID="bad id\nwith spaces")
    # Invalid -> a fresh generated id is used instead.
    assert resp["X-Request-ID"] != "bad id\nwith spaces"
    assert re.fullmatch(r"[0-9a-f]{32}", resp["X-Request-ID"])


def test_rejects_overlong_incoming_header(client):
    with override_settings(TRACEID={"INCOMING_MAX_LENGTH": 5}):
        resp = client.get("/echo/", HTTP_X_REQUEST_ID="toolong")
    assert re.fullmatch(r"[0-9a-f]{32}", resp["X-Request-ID"])


def test_context_cleared_after_request(client):
    client.get("/echo/")
    assert get_trace_id() is None


@override_settings(TRACEID={"TRUST_INCOMING_HEADER": False})
def test_ignores_incoming_when_untrusted(client):
    resp = client.get("/echo/", HTTP_X_REQUEST_ID="should-be-ignored")
    assert resp["X-Request-ID"] != "should-be-ignored"


@override_settings(TRACEID={"RESPONSE_HEADER": "X-Correlation-ID"})
def test_custom_response_header(client):
    resp = client.get("/echo/")
    assert "X-Correlation-ID" in resp


@override_settings(TRACEID={"SENTRY_TAG": True})
def test_sentry_tag_enabled_does_not_crash(client):
    # sentry_sdk is not installed in the test env: the import guard must swallow it.
    resp = client.get("/echo/")
    assert resp.status_code == 200
