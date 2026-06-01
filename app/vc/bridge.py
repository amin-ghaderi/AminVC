"""E5.2 — Bridge worker IPC progress to VcProgressAdapter."""

from __future__ import annotations

import logging
from typing import Any

from app.contracts.worker_messages import ProgressResponse, parse_progress
from app.vc.progress_adapter import VcProgressAdapter

logger = logging.getLogger(__name__)


class VcProgressBridge:
    """Maps worker `progress` JSONL messages to adapter step updates."""

    def __init__(self, adapter: VcProgressAdapter) -> None:
        self._adapter = adapter
        self._last_step = 0

    def on_progress_message(self, message: dict[str, Any] | ProgressResponse) -> None:
        try:
            progress = (
                message
                if isinstance(message, ProgressResponse)
                else parse_progress(message)
            )
            if progress.current_step == self._last_step:
                return
            self._last_step = progress.current_step
            self._adapter.update_step(progress.current_step)
        except Exception:
            logger.warning(
                "VC progress bridge update failed",
                exc_info=True,
            )
