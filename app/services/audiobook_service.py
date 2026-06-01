"""
AudiobookService: minimal sequential orchestrator (Phase 2C).

Flow:
    PDF → NarrationService.generate_chunks()
        → WorkerSpeakerService.convert_chunk() (sequential)
        → PCM WAV merge (stdlib wave)
        → final export

Explicit non-goals:
- no UI, parallelism, retries, threading, pipeline state machine
"""

from __future__ import annotations

import logging
import time
import traceback
import wave
from dataclasses import dataclass, field
from pathlib import Path

from app.config.settings import AppSettings
from app.services.narration_service import NarrationService
from app.services.speaker_service import WorkerSpeakerService


logger = logging.getLogger(__name__)

WAV_MERGE_CHUNK_FRAMES = 8192


@dataclass(frozen=True, slots=True)
class AudiobookResult:
    success: bool
    chunk_count: int
    converted_chunks: int
    duration_seconds: float
    output_path: Path
    failed_chunk: str | None = None


@dataclass(slots=True)
class AudiobookService:
    narration: NarrationService = field(default_factory=NarrationService)
    speaker: WorkerSpeakerService = field(default_factory=WorkerSpeakerService)
    settings: AppSettings = field(default_factory=AppSettings)

    @property
    def _speaker_temp_dir(self) -> Path:
        return self.settings.storage_root / "temp" / "speaker"

    def create_audiobook(
        self,
        pdf_path: Path,
        reference_voice_path: Path,
        output_path: Path,
    ) -> AudiobookResult:
        pdf_path = Path(pdf_path)
        reference_voice_path = Path(reference_voice_path)
        output_path = Path(output_path)

        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path.resolve()))
        if not reference_voice_path.exists():
            raise FileNotFoundError(str(reference_voice_path.resolve()))

        started = time.time()
        chunk_count = 0
        converted_chunks = 0
        failed_chunk: str | None = None

        try:
            manifest = self.narration.generate_chunks(pdf_path)
            chunk_paths = sorted(
                manifest.chunk_audio_paths,
                key=lambda p: int(p.stem),
            )
            chunk_count = len(chunk_paths)
            print(f"Narration chunks: {chunk_count}")

            if chunk_count == 0:
                raise RuntimeError("Narration produced no chunk WAV paths.")

            self._speaker_temp_dir.mkdir(parents=True, exist_ok=True)
            converted_paths: list[Path] = []

            for index, source_path in enumerate(chunk_paths, start=1):
                name = source_path.name
                speaker_out = self._speaker_temp_dir / name
                print(f"[{index}/{chunk_count}] converting {name}")
                try:
                    self.speaker.convert_chunk(
                        source_path,
                        reference_voice_path,
                        speaker_out,
                    )
                except Exception as exc:
                    failed_chunk = name
                    logger.error("Speaker conversion failed for %s: %s", name, exc)
                    return AudiobookResult(
                        success=False,
                        chunk_count=chunk_count,
                        converted_chunks=converted_chunks,
                        duration_seconds=time.time() - started,
                        output_path=output_path,
                        failed_chunk=failed_chunk,
                    )

                converted_chunks += 1
                converted_paths.append(speaker_out.resolve())
                print(f"[{index}/{chunk_count}] complete")

            print(f"Merging {len(converted_paths)} chunks...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            merge_pcm_wavs(converted_paths, output_path.resolve())
            print("Merge complete")

            return AudiobookResult(
                success=True,
                chunk_count=chunk_count,
                converted_chunks=converted_chunks,
                duration_seconds=time.time() - started,
                output_path=output_path.resolve(),
            )
        finally:
            self.speaker.shutdown()


def merge_pcm_wavs(chunk_paths: list[Path], output_path: Path) -> None:
    """
    Concatenate PCM WAV files with identical parameters (stdlib wave only).
    """
    if not chunk_paths:
        raise ValueError("No WAV chunks to merge.")

    with wave.open(str(chunk_paths[0]), "rb") as first:
        params = first.getparams()

    nchannels, sampwidth, framerate, _, comptype, compname = params
    if comptype != "NONE":
        raise ValueError(f"Unsupported WAV compression: {comptype!r}")

    for path in chunk_paths[1:]:
        with wave.open(str(path), "rb") as w:
            other = w.getparams()
            if (
                w.getnchannels() != nchannels
                or w.getsampwidth() != sampwidth
                or w.getframerate() != framerate
                or w.getcomptype() != comptype
            ):
                raise ValueError(
                    f"Incompatible WAV parameters for {path.name}: "
                    f"expected nchannels={nchannels}, sampwidth={sampwidth}, "
                    f"framerate={framerate}, comptype={comptype!r}; got {other}"
                )

    output_path = Path(output_path)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(tmp_path), "wb") as out:
        out.setparams(params)
        for path in chunk_paths:
            with wave.open(str(path), "rb") as src:
                while True:
                    frames = src.readframes(WAV_MERGE_CHUNK_FRAMES)
                    if not frames:
                        break
                    out.writeframesraw(frames)

    tmp_path.replace(output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        settings = AppSettings()
        pdf_path = settings.storage_root / "input" / "test.pdf"
        reference_path = settings.storage_root / "phase2a_ref.wav"
        output_path = settings.storage_root / "exports" / "final_audiobook.wav"

        if not pdf_path.exists():
            raise FileNotFoundError(f"Proof PDF missing: {pdf_path}")
        if not reference_path.exists():
            raise FileNotFoundError(f"Proof reference WAV missing: {reference_path}")

        svc = AudiobookService()
        result = svc.create_audiobook(pdf_path, reference_path, output_path)

        print(
            "Summary:",
            f"success={result.success}",
            f"chunks={result.chunk_count}",
            f"converted={result.converted_chunks}",
            f"duration_seconds={result.duration_seconds:.1f}",
            f"output={result.output_path}",
        )
        if result.failed_chunk:
            print(f"failed_chunk={result.failed_chunk}")
        if not result.success:
            raise SystemExit(1)
    except Exception:
        traceback.print_exc()
        raise
