"""
Structured JSON diagnostics for Google Gemini TTS API calls (Phase S1).

Observability only — never raises to callers.
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config.settings import get_settings

logger = logging.getLogger(__name__)

_PROVIDER = "google_gemini"
_ENDPOINT_TEMPLATE = "models/{model}:generateContent"
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def persist_tts_api_event(
    *,
    model: str,
    voice: str,
    token_name: str,
    attempt_number: int,
    text_length: int,
    elapsed_ms: float,
    success: bool,
    chunk_id: int | None = None,
    intake_id: str | None = None,
    status_code: int | None = None,
    google_error_status: str | None = None,
    google_error_message: str | None = None,
    token_switch_reason: str | None = None,
    request_id: str | None = None,
    exception: BaseException | None = None,
) -> None:
    """Write one structured API event JSON file; failures are swallowed."""
    try:
        event = _build_event(
            model=model,
            voice=voice,
            token_name=token_name,
            attempt_number=attempt_number,
            text_length=text_length,
            elapsed_ms=elapsed_ms,
            success=success,
            chunk_id=chunk_id,
            intake_id=intake_id,
            status_code=status_code,
            google_error_status=google_error_status,
            google_error_message=google_error_message,
            token_switch_reason=token_switch_reason,
            request_id=request_id,
            exception=exception,
        )
        path = _event_path(event["timestamp"], token_name, attempt_number, chunk_id, intake_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug("TTS API event saved: %s", path)
    except Exception as exc:
        logger.warning("TTS API event persist failed (non-fatal): %s", exc)


def extract_google_error_fields(exc: BaseException | None) -> tuple[int | None, str | None, str | None]:
    """Best-effort status_code, google status string, and message from SDK/HTTP errors."""
    if exc is None:
        return None, None, None

    status_code: int | None = None
    for attr in ("code", "status_code", "status"):
        raw = getattr(exc, attr, None)
        if isinstance(raw, int):
            status_code = raw
            break
        if isinstance(raw, str) and raw.isdigit():
            status_code = int(raw)
            break

    google_status: str | None = None
    google_message: str | None = None

    response = getattr(exc, "response", None)
    if response is not None:
        status_code = status_code or getattr(response, "status_code", None)
        try:
            body = response.json() if hasattr(response, "json") else None
            if isinstance(body, dict) and "error" in body:
                err = body["error"]
                if isinstance(err, dict):
                    google_status = err.get("status") or google_status
                    google_message = err.get("message") or google_message
                    if status_code is None and err.get("code") is not None:
                        try:
                            status_code = int(err["code"])
                        except (TypeError, ValueError):
                            pass
        except Exception:
            pass

    message = str(exc).strip()
    if not google_message:
        google_message = message[:2000] if message else None

    upper = message.upper()
    if google_status is None:
        for token in ("RESOURCE_EXHAUSTED", "INTERNAL", "UNAVAILABLE", "INVALID_ARGUMENT"):
            if token in upper:
                google_status = token
                break

    if status_code is None:
        for code in (429, 500, 503, 400, 401, 403, 404):
            if str(code) in message:
                status_code = code
                break

    return status_code, google_status, google_message


def extract_request_id(response: Any) -> str | None:
    """Best-effort request id from a generate_content response object."""
    if response is None:
        return None
    for attr in ("request_id", "requestId"):
        value = getattr(response, attr, None)
        if value:
            return str(value)
    sdk_http = getattr(response, "sdk_http_response", None)
    if sdk_http is not None:
        headers = getattr(sdk_http, "headers", None) or {}
        if isinstance(headers, dict):
            for key in ("x-goog-request-id", "x-request-id", "request-id"):
                if key in headers:
                    return str(headers[key])
                for hk, hv in headers.items():
                    if str(hk).lower() == key:
                        return str(hv)
    return None


def _build_event(
    *,
    model: str,
    voice: str,
    token_name: str,
    attempt_number: int,
    text_length: int,
    elapsed_ms: float,
    success: bool,
    chunk_id: int | None,
    intake_id: str | None,
    status_code: int | None,
    google_error_status: str | None,
    google_error_message: str | None,
    token_switch_reason: str | None,
    request_id: str | None,
    exception: BaseException | None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    event: dict[str, Any] = {
        "timestamp": now.isoformat(),
        "provider": _PROVIDER,
        "endpoint": _ENDPOINT_TEMPLATE.format(model=model),
        "model": model,
        "voice": voice,
        "token_name": token_name,
        "attempt_number": attempt_number,
        "text_length": text_length,
        "elapsed_ms": round(elapsed_ms, 2),
        "success": success,
        "status_code": status_code,
        "google_error_status": google_error_status,
        "google_error_message": google_error_message,
        "token_switch_reason": token_switch_reason,
        "request_id": request_id,
        "chunk_id": chunk_id,
        "intake_id": intake_id,
    }
    if not success and exception is not None:
        event["exception_traceback"] = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )
    return event


def _event_path(
    timestamp_iso: str,
    token_name: str,
    attempt_number: int,
    chunk_id: int | None,
    intake_id: str | None,
) -> Path:
    day = timestamp_iso[:10]
    safe_token = _SAFE_NAME.sub("_", token_name)[:40] or "token"
    chunk_part = f"{chunk_id:04d}" if chunk_id is not None else "na"
    intake_part = _SAFE_NAME.sub("_", intake_id or "na")[:36]
    unique = uuid.uuid4().hex[:8]
    name = f"{int(time.time() * 1000)}_{intake_part}_{chunk_part}_a{attempt_number}_{safe_token}_{unique}.json"
    return get_settings().storage_root / "debug" / "api_events" / day / name


if __name__ == "__main__":
    # Tiny proof: write one synthetic failed event (no live API key required).
    persist_tts_api_event(
        model="gemini-3.1-flash-tts-preview",
        voice="Sulafat",
        token_name="project-proof",
        attempt_number=1,
        text_length=42,
        elapsed_ms=1234.5,
        success=False,
        chunk_id=3,
        intake_id="proof-intake",
        status_code=500,
        google_error_status="INTERNAL",
        google_error_message="Internal error encountered.",
        token_switch_reason="transient_error",
        request_id=None,
        exception=RuntimeError("500 INTERNAL"),
    )
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root = get_settings().storage_root / "debug" / "api_events" / day
    latest = max(root.glob("*.json"), key=lambda p: p.stat().st_mtime, default=None)
    if latest:
        print(latest.read_text(encoding="utf-8"))
    else:
        print("No event file written.")
