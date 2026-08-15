from __future__ import annotations

import re

import pytest
from django.test import AsyncClient, Client, override_settings

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


def test_streaming_response_keeps_id_until_body_consumed(client):
    """The id read inside the generator must match the echoed header (streaming bug)."""
    resp = client.get("/stream/")
    rid = resp["X-Request-ID"]
    body = b"".join(resp.streaming_content).decode()
    assert body == rid
    assert re.fullmatch(r"[0-9a-f]{32}", rid)


def test_streaming_response_clears_context_after_consumption(client):
    resp = client.get("/stream/")
    b"".join(resp.streaming_content)
    assert get_trace_id() is None


def test_async_middleware_binds_id():
    """Under an async handler the middleware still binds/echoes the id (ASGI path)."""
    from asgiref.sync import async_to_sync

    resp = async_to_sync(AsyncClient().get)("/aecho/")
    rid = resp["X-Request-ID"]
    assert resp.content.decode() == rid
    assert re.fullmatch(r"[0-9a-f]{32}", rid)


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


@override_settings(TRACEID={"SENTRY_TAG": True})
def test_sentry_tag_set_when_sdk_present(client, monkeypatch):
    # Inject a stand-in sentry_sdk so the import guard succeeds and the tag
    # is set with the request's trace id.
    import sys
    import types

    calls: list[tuple[str, str]] = []
    fake_sentry = types.ModuleType("sentry_sdk")
    fake_sentry.set_tag = lambda key, value: calls.append((key, value))
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry)

    resp = client.get("/echo/")

    assert resp.status_code == 200
    assert calls == [("trace_id", resp["X-Request-ID"])]


@override_settings(TRACEID={"SENTRY_TAG": True})
def test_sentry_tag_uses_isolation_scope_when_available(client, monkeypatch):
    # Modern sentry-sdk (>=2.0) exposes get_isolation_scope: the tag must land
    # on the per-request scope, not the global one.
    import sys
    import types

    calls: list[tuple[str, str]] = []

    class _Scope:
        def set_tag(self, key: str, value: str) -> None:
            calls.append((key, value))

    scope = _Scope()
    fake_sentry = types.ModuleType("sentry_sdk")
    fake_sentry.get_isolation_scope = lambda: scope
    fake_sentry.set_tag = lambda key, value: calls.append(("GLOBAL", value))
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry)

    resp = client.get("/echo/")

    assert resp.status_code == 200
    # Isolation-scope path used; global set_tag never touched.
    assert calls == [("trace_id", resp["X-Request-ID"])]
