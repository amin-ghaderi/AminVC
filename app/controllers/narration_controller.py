"""
Narration controller placeholder (Phase 1).

Defines intended controller-level entrypoints for narration-related actions.
No engine calls and no orchestration in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class NarrationController:
    def upload_pdf(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def update_text(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def preview_chunks(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def generate_narration(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

