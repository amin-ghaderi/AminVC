"""
E0 canonical chunk/part state machine.

Only these states are valid. No other states are allowed.
"""

from __future__ import annotations

from typing import Final

# Valid states (exact spelling per E0 specification).
STATE_DRAFT: Final = "Draft"
STATE_TEXT_SAVED: Final = "TextSaved"

STATE_NARRATION_QUEUED: Final = "NarrationQueued"
STATE_NARRATION_PROCESSING: Final = "NarrationProcessing"
STATE_NARRATION_READY: Final = "NarrationReady"
STATE_NARRATION_APPROVED: Final = "NarrationApproved"

STATE_VC_QUEUED: Final = "VCQueued"
STATE_VC_PROCESSING: Final = "VCProcessing"
STATE_VC_READY: Final = "VCReady"
STATE_VC_APPROVED: Final = "VCApproved"

STATE_BUILD_READY: Final = "BuildReady"

STATE_NARRATION_FAILED: Final = "NarrationFailed"
STATE_VC_FAILED: Final = "VCFailed"

STATE_INTERRUPTED: Final = "Interrupted"

VALID_CHUNK_STATES: frozenset[str] = frozenset(
    {
        STATE_DRAFT,
        STATE_TEXT_SAVED,
        STATE_NARRATION_QUEUED,
        STATE_NARRATION_PROCESSING,
        STATE_NARRATION_READY,
        STATE_NARRATION_APPROVED,
        STATE_VC_QUEUED,
        STATE_VC_PROCESSING,
        STATE_VC_READY,
        STATE_VC_APPROVED,
        STATE_BUILD_READY,
        STATE_NARRATION_FAILED,
        STATE_VC_FAILED,
        STATE_INTERRUPTED,
    }
)

# Part-level state uses the same vocabulary (E0).
VALID_PART_STATES: frozenset[str] = VALID_CHUNK_STATES

PROJECT_STATUS_ACTIVE: Final = "active"
