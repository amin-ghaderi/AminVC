"""Stable device_id for the local agent (not project storage)."""

from __future__ import annotations

import os
import uuid
from pathlib import Path


def load_or_create_device_id(path: Path, override: str | None = None) -> str:
    explicit = (override if override is not None else os.environ.get("AMINVC_DEVICE_ID", "")).strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    if explicit:
        path.write_text(explicit, encoding="utf-8")
        return explicit
    if path.is_file():
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    device_id = uuid.uuid4().hex
    path.write_text(device_id, encoding="utf-8")
    return device_id
