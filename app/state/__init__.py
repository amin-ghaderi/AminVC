"""
Runtime state package (Phase 1).

Architecture correction:
- `app/contracts/` contains schemas/DTOs/interfaces (stable contracts)
- `app/state/` is reserved for runtime lifecycle, transitions, and execution state (later phases)

Phase 1 includes compatibility re-exports only.
"""

from __future__ import annotations

