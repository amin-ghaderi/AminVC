"""
Compatibility re-export (Phase 1 architecture correction).

Runtime lifecycle belongs in `app/state/`. Schema/contracts belong in `app/contracts/`.

This module remains to avoid breaking older imports:
`from app.state.project_state import ProjectState`
"""

from __future__ import annotations

from app.contracts.project import ProjectState

__all__ = ["ProjectState"]

