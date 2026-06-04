"""E5.2 — Bridge worker IPC progress to VcProgressAdapter."""

from __future__ import annotations

import logging
from typing import Any

from app.contracts.worker_messages import ProgressResponse, parse_progress
from app.vc.progress_adapter import VcProgressAdapter

logger = logging.getLogger(__name__)


class VcProgressBridge:
    """Maps worker `progress` JSONL messages to adapter progress updates."""

    def __init__(self, adapter: VcProgressAdapter) -> None:
        self._adapter = adapter
        self._last_key: tuple[int, int, int, int] | None = None

    def on_progress_message(self, message: dict[str, Any] | ProgressResponse) -> None:
        try:
            progress = (
                message
                if isinstance(message, ProgressResponse)
                else parse_progress(message)
            )
            seg_idx = progress.segment_index if progress.segment_index > 0 else 0
            seg_tot = progress.segment_total if progress.segment_total > 0 else 0
            key = (
                progress.current_step,
                progress.total_steps,
                seg_idx,
                seg_tot,
            )
            if key == self._last_key:
                return
            self._last_key = key
            self._adapter.update_progress(
                progress.current_step,
                progress.total_steps,
                progress.segment_index if progress.segment_index > 0 else None,
                progress.segment_total if progress.segment_total > 0 else None,
            )
        except Exception:
            logger.warning(
                "VC progress bridge update failed",
                exc_info=True,
            )
