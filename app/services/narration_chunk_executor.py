"""
Per-chunk narration execution boundary (E6 / E6.1).

NarrationService.generate_chunks() remains PDF-batch oriented; executors here
handle single-chunk jobs for the worker engine.
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from app.contracts.manifests import ChunkManifest
from app.narration import bridge
from app.narration.events import (
    publish_chunk_completed,
    publish_chunk_failed,
    publish_chunk_started,
)
from app.narration.exceptions import (
    NarrationChunkExecutionError,
    NarrationEngineUnavailableError,
)

if TYPE_CHECKING:
    from app.events.bus import EventBus

# Placeholder WAV is ~4844 bytes (44-byte header + 4800 zero samples).
_PLACEHOLDER_MAX_BYTES = 8_000


class NarrationChunkExecutor(Protocol):
    def generate_chunk(
        self,
        *,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
        output_path: Path,
    ) -> Path:
        ...


class WaveNarrationChunkExecutor:
    """Writes a minimal PCM WAV (tests / offline when Gemini TTS is unavailable)."""

    def generate_chunk(
        self,
        *,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
        output_path: Path,
    ) -> Path:
        del project_id, part_id, chunk
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            handle.writeframes(b"\x00\x00" * 2400)
        return output_path


class GeminiNarrationChunkExecutor:
    """
    E6.1 — Real Gemini TTS per chunk via narration-engine `generate_audio`.

    Uses ChunkManifest.text as the sole transcript source (no PDF reload).
    """

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus

    def generate_chunk(
        self,
        *,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
        output_path: Path,
    ) -> Path:
        text = (chunk.text or "").strip()
        if not text:
            raise NarrationChunkExecutionError("ChunkManifest.text is empty")

        status = bridge.check_narration_engine_ready()
        if not status.ready:
            raise NarrationEngineUnavailableError(
                status.message or "Narration engine unavailable"
            )

        publish_chunk_started(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk.chunk_id,
        )

        try:
            bridge.synthesize_chunk_text(text, output_path)
        except NarrationEngineUnavailableError:
            publish_chunk_failed(
                self._event_bus,
                project_id=project_id,
                part_id=part_id,
                chunk_id=chunk.chunk_id,
                error="Narration engine unavailable",
            )
            raise
        except Exception as exc:
            message = str(exc)
            publish_chunk_failed(
                self._event_bus,
                project_id=project_id,
                part_id=part_id,
                chunk_id=chunk.chunk_id,
                error=message,
            )
            raise NarrationChunkExecutionError(message) from exc

        if not output_path.is_file():
            publish_chunk_failed(
                self._event_bus,
                project_id=project_id,
                part_id=part_id,
                chunk_id=chunk.chunk_id,
                error="Narration output file missing",
            )
            raise NarrationChunkExecutionError("Narration output file missing")

        size = output_path.stat().st_size
        if size == 0:
            publish_chunk_failed(
                self._event_bus,
                project_id=project_id,
                part_id=part_id,
                chunk_id=chunk.chunk_id,
                error="Narration output file is empty",
            )
            raise NarrationChunkExecutionError("Narration output file is empty")

        if size <= _PLACEHOLDER_MAX_BYTES and _is_silent_wav(output_path):
            publish_chunk_failed(
                self._event_bus,
                project_id=project_id,
                part_id=part_id,
                chunk_id=chunk.chunk_id,
                error="Narration output appears to be placeholder silence",
            )
            raise NarrationChunkExecutionError(
                "Narration output appears to be placeholder silence"
            )

        publish_chunk_completed(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk.chunk_id,
            duration_seconds=_wav_duration_seconds(output_path),
        )
        return output_path


def _wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        if rate <= 0:
            return 0.0
        return handle.getnframes() / float(rate)


def _is_silent_wav(path: Path) -> bool:
    with wave.open(str(path), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
        sample_width = handle.getsampwidth()
        channels = handle.getnchannels()
    if not frames:
        return True
    step = sample_width * channels
    zero = b"\x00" * sample_width
    for offset in range(0, len(frames), step):
        if frames[offset : offset + sample_width] != zero:
            return False
    return True
