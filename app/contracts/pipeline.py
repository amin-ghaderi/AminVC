"""
Pipeline state contract (Contract v1).

Phase 1 scope: allowed states only.
No transition logic. No persistence. No hidden states.
"""

from __future__ import annotations

from enum import Enum


class PipelineState(str, Enum):
    created = "created"
    uploaded = "uploaded"
    repaired = "repaired"
    chunked = "chunked"
    tts_generating = "tts_generating"
    tts_completed = "tts_completed"
    speaker_conversion = "speaker_conversion"
    speaker_completed = "speaker_completed"
    merging = "merging"
    mastering = "mastering"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

