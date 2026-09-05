"""In-memory last-heartbeat store. Not durable across process restarts."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str | None) -> datetime:
    if not value or not value.strip():
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return utc_now()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class HeartbeatStore:
    def __init__(self, *, online_timeout_seconds: float = 30.0) -> None:
        self.online_timeout_seconds = online_timeout_seconds
        self._lock = threading.Lock()
        self._last_seen: dict[str, datetime] = {}

    def record(self, device_id: str, timestamp: str | None = None) -> datetime:
        seen = parse_timestamp(timestamp)
        with self._lock:
            self._last_seen[device_id] = seen
        return seen

    def status(
        self,
        device_id: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        moment = now or utc_now()
        with self._lock:
            last_seen = self._last_seen.get(device_id)
        if last_seen is None:
            return {
                "device_id": device_id,
                "online": False,
                "last_seen": None,
            }
        age = (moment - last_seen).total_seconds()
        return {
            "device_id": device_id,
            "online": age <= self.online_timeout_seconds,
            "last_seen": last_seen.isoformat(),
        }
