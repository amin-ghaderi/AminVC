"""Outbound HTTPS heartbeat from the local FastAPI process. Must not crash the API."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

import httpx

from app.config.settings import AppSettings

logger = logging.getLogger(__name__)


class AgentHeartbeatService:
    def __init__(
        self,
        settings: AppSettings,
        device_id: str,
        *,
        cloud_url: str | None = None,
        post=None,
    ) -> None:
        self._settings = settings
        self._device_id = device_id
        self._cloud_url = (cloud_url if cloud_url is not None else settings.agent_cloud_url).rstrip(
            "/"
        )
        self._post = post or httpx.post
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def start(self) -> None:
        if not self._cloud_url:
            logger.info("Agent heartbeat disabled (no agent_cloud_url)")
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="aminvc-agent-heartbeat",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Agent heartbeat started device_id=%s cloud=%s",
            self._device_id,
            self._cloud_url,
        )

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._thread = None

    def send_once(self) -> bool:
        if not self._cloud_url:
            return False
        url = f"{self._cloud_url}/agent/heartbeat"
        payload = {
            "device_id": self._device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
        }
        try:
            response = self._post(url, json=payload, timeout=5.0)
            if getattr(response, "status_code", 200) >= 400:
                logger.warning(
                    "Agent heartbeat rejected status=%s",
                    getattr(response, "status_code", "?"),
                )
                return False
            return True
        except Exception:
            logger.warning("Agent heartbeat failed; agent stays running", exc_info=True)
            return False

    def _loop(self) -> None:
        interval = max(1.0, float(self._settings.agent_heartbeat_interval_seconds))
        self.send_once()
        while not self._stop.wait(interval):
            self.send_once()
