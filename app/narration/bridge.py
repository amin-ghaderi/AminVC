"""
E6.1 — Bridge to narration-engine Gemini TTS (Option A: direct `generate_audio`).

Uses narration-engine config and token pool as the single source of truth.
Does not duplicate API keys or voice settings.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config.settings import PROJECT_ROOT

logger = logging.getLogger(__name__)

NARRATION_ENGINE_BACKEND_ROOT = PROJECT_ROOT / "narration-engine" / "backend"


@dataclass(frozen=True, slots=True)
class NarrationEngineStatus:
    ready: bool
    message: str = ""


def ensure_narration_engine_path() -> None:
    path = str(NARRATION_ENGINE_BACKEND_ROOT.resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


@lru_cache(maxsize=1)
def _narration_settings():
    ensure_narration_engine_path()
    from backend.config.settings import get_settings

    return get_settings()


def check_narration_engine_ready() -> NarrationEngineStatus:
    """Verify tokens and narration-engine modules are available (no HTTP required)."""
    try:
        ensure_narration_engine_path()
        from backend.services.token_config import load_enabled_tokens

        settings = _narration_settings()
        tokens = load_enabled_tokens(settings.tokens_file)
        if not tokens:
            return NarrationEngineStatus(
                ready=False,
                message="Narration engine unavailable: no Gemini API tokens configured",
            )
        return NarrationEngineStatus(ready=True)
    except Exception as exc:
        logger.debug("narration engine readiness check failed", exc_info=True)
        return NarrationEngineStatus(
            ready=False,
            message=f"Narration engine unavailable: {exc}",
        )


def create_token_pool():
    """Return a narration-engine TokenPool using projects.json (or GEMINI_API_KEY)."""
    ensure_narration_engine_path()
    from backend.services.token_pool import TokenPool

    settings = _narration_settings()
    pool = TokenPool(settings.tokens_file)
    if pool.total == 0:
        raise RuntimeError("No Gemini API tokens configured")
    return pool


def synthesize_chunk_text(text: str, output_path: Path) -> None:
    """
    Generate one chunk WAV via narration-engine `generate_audio`.

    Writes directly to `output_path` (E0 canonical path).
    """
    ensure_narration_engine_path()
    from backend.services.gemini_tts import generate_audio
    from backend.services.token_pool import GenerationCancelled

    output_path.parent.mkdir(parents=True, exist_ok=True)
    token_pool = create_token_pool()
    try:
        generate_audio(text.strip(), str(output_path), token_pool)
    except GenerationCancelled as exc:
        raise RuntimeError(f"Narration cancelled: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Narration synthesis failed: {exc}") from exc
