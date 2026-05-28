"""
Compatibility re-export (Phase 1 architecture correction).

Runtime state must live under `app/state/`, while schema/contracts live under
`app/contracts/`.

This module remains to avoid breaking older imports:
`from app.state.pipeline_states import PipelineState`
"""

from __future__ import annotations

from app.contracts.pipeline import PipelineState

__all__ = ["PipelineState"]

