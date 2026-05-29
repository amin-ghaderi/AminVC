"""Phase T1 — fail-fast HTTP timeout selection for Gemini TTS."""

from backend.services.gemini_tts import (
    _TTS_FAIL_FAST_MAX_ADDITIONAL_TOKENS,
    _TTS_FAIL_FAST_TIMEOUT_MS,
    _config_for_tts_request,
    _is_transport_timeout_error,
    _is_transient_failover_error,
    _should_use_fail_fast_http_timeout,
)
from google.genai import types


def test_first_token_on_chunk_no_fail_fast():
    assert _should_use_fail_fast_http_timeout(set()) is False


def test_fail_fast_after_first_transient_up_to_cap():
    failed = {"project-1"}
    assert _should_use_fail_fast_http_timeout(failed) is True
    for i in range(2, _TTS_FAIL_FAST_MAX_ADDITIONAL_TOKENS + 1):
        failed.add(f"project-{i}")
        assert _should_use_fail_fast_http_timeout(failed) is True
    failed.add(f"project-{_TTS_FAIL_FAST_MAX_ADDITIONAL_TOKENS + 1}")
    assert _should_use_fail_fast_http_timeout(failed) is False


def test_fail_fast_config_sets_http_timeout():
    base = types.GenerateContentConfig(temperature=1)
    merged = _config_for_tts_request(base, fail_fast=True)
    assert merged.http_options is not None
    assert merged.http_options.timeout == _TTS_FAIL_FAST_TIMEOUT_MS


def test_success_config_unchanged_without_fail_fast():
    base = types.GenerateContentConfig(temperature=1)
    assert _config_for_tts_request(base, fail_fast=False) is base


def test_transport_timeout_is_transient():
    assert _is_transport_timeout_error(TimeoutError("read timed out"))
    assert _is_transient_failover_error(TimeoutError("read timed out"))


def test_internal_still_transient():
    assert _is_transient_failover_error(RuntimeError("500 INTERNAL"))
