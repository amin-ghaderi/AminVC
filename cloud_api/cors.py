"""CORS origins for the public heartbeat API. Never use a wildcard."""

from __future__ import annotations

import os

LOCAL_DEV_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


def resolve_cors_origins(raw: str | None = None) -> list[str]:
    text = (raw if raw is not None else os.environ.get("AMINVC_WEB_ORIGIN", "")).strip()
    configured = [part.strip().rstrip("/") for part in text.split(",") if part.strip()]
    if configured:
        return configured
    return list(LOCAL_DEV_ORIGINS)
