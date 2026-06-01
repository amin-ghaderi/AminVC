"""E6.1 narration integration errors."""

from __future__ import annotations


class NarrationEngineUnavailableError(RuntimeError):
    """Raised when narration-engine cannot run (missing tokens, import failure)."""


class NarrationChunkExecutionError(RuntimeError):
    """Raised when per-chunk TTS synthesis fails."""
