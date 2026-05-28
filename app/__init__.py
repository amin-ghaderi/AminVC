"""
AminVC application layer (Phase 1 skeleton).

This package is the future orchestration layer for AminVC. In Phase 1, it contains
ONLY contracts (types/interfaces/models) and placeholders. It intentionally does
NOT implement any orchestration logic, engine calls, persistence, UI integration,
or audio merging behavior.

Critical boundary rule (Contract v1):
- `app/` orchestrates
- `narration-engine/` and `speaker-engine/` remain isolated domain engines
- no engine-to-engine imports, and `app/` must not embed engine internals
"""

from __future__ import annotations

