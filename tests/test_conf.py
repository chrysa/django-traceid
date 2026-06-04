from __future__ import annotations

import pytest
from django.test import override_settings

from django_traceid.conf import DEFAULTS, traceid_settings


def test_unknown_setting_raises_attribute_error():
    unknown = "NOT_A_REAL_SETTING"
    with pytest.raises(AttributeError, match="Invalid TRACEID setting"):
        getattr(traceid_settings, unknown)


def test_default_used_without_user_override():
    assert traceid_settings.REQUEST_HEADER == DEFAULTS["REQUEST_HEADER"]


@override_settings(TRACEID={"REQUEST_HEADER": "X-Custom-ID"})
def test_user_value_overrides_default():
    assert traceid_settings.REQUEST_HEADER == "X-Custom-ID"


def test_reload_on_setting_changed_refreshes_cache():
    # Prime the cache with the default, then override: the setting_changed
    # signal must clear the cache so the new value is returned.
    assert traceid_settings.REQUEST_HEADER == DEFAULTS["REQUEST_HEADER"]
    with override_settings(TRACEID={"REQUEST_HEADER": "X-Reloaded"}):
        assert traceid_settings.REQUEST_HEADER == "X-Reloaded"
    # Leaving the override fires the signal again and restores the default.
    assert traceid_settings.REQUEST_HEADER == DEFAULTS["REQUEST_HEADER"]


@override_settings(TRACEID={"REQUEST_HEADER": "X-Correlation-ID"})
def test_request_meta_key_derives_from_request_header():
    assert traceid_settings.request_meta_key == "HTTP_X_CORRELATION_ID"
