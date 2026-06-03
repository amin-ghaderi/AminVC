"""
SpeakerService: minimal-risk worker-backed integration (Phase 2A).

Scope:
- Wrap the already-working JSONL worker (`SpeakerWorkerClient`) behind a small service surface.
- Persistent worker lifecycle (lazy start, reuse, shutdown).
- Health validation on startup.
- Minimal recycle policy (max conversions per worker).

Explicit non-goals:
- no orchestration
- no pipeline logic
- no manifests
- no merge
- no speaker-engine imports
"""

from __future__ import annotations

import json
import logging
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.events.bus import EventBus
from app.vc.bridge import VcProgressBridge
from app.vc.progress_adapter import VcProgressAdapter
from app.workers.speaker_worker_client import SpeakerWorkerClient


logger = logging.getLogger(__name__)


class SpeakerService(Protocol):
    """
    Interface boundary for speaker-engine.

    Phase 2A: worker-backed runtime capability only.
    """

    def start(self) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError

    def health(self) -> dict[str, Any]:
        raise NotImplementedError

    def convert_chunk(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        settings: dict[str, Any] | None = None,
    ) -> Path:
        raise NotImplementedError

@dataclass(slots=True)
class WorkerSpeakerService:
    """
    Production-safe minimal wrapper around `SpeakerWorkerClient`.

    - Long-lived worker lifecycle (lazy start, reused across conversions)
    - Health validation on startup
    - Minimal recycle policy to bound long-run memory growth
    """

    max_conversions_per_worker: int = 25
    python_executable: str | None = None
    _client: SpeakerWorkerClient | None = None
    _conversions_since_start: int = 0
    _last_worker_pid: int | None = None

    def _ensure_client(self) -> SpeakerWorkerClient:
        if self._client is None:
            self._client = SpeakerWorkerClient(
                python_executable=(self.python_executable or SpeakerWorkerClient().python_executable)
            )
        return self._client

    def _worker_running(self) -> bool:
        if self._client is None or self._client.process is None:
            return False
        return self._client.process.poll() is None

    def start(self) -> None:
        client = self._ensure_client()
        if not self._worker_running():
            logger.info("Speaker worker starting")
        start_payload = client.start()

        # Record PID when available (used for proof visibility / reuse check)
        if client.process is not None:
            self._last_worker_pid = client.process.pid

        health = client.health()
        if not (isinstance(health, dict) and health.get("ready") is True):
            raise RuntimeError(f"Speaker worker failed health check: {health}")
        logger.info("Speaker worker healthy")

    def shutdown(self) -> None:
        if self._client is None:
            return
        if self._client.process is None or self._client.process.poll() is not None:
            self._client = None
            self._conversions_since_start = 0
            self._last_worker_pid = None
            return

        logger.info("Speaker worker shutdown requested")
        try:
            self._client.shutdown()
        finally:
            self._client = None
            self._conversions_since_start = 0
            self._last_worker_pid = None
        logger.info("Speaker worker shutdown complete")

    def health(self) -> dict[str, Any]:
        self.start()
        assert self._client is not None
        return self._client.health()

    def _maybe_recycle(self) -> None:
        if self.max_conversions_per_worker <= 0:
            return
        if self._conversions_since_start < self.max_conversions_per_worker:
            return
        logger.info("Speaker worker recycle (max conversions reached)")
        self.shutdown()
        self.start()
        self._conversions_since_start = 0

    def convert_chunk(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        settings: dict[str, Any] | None = None,
        *,
        project_id: str | None = None,
        part_id: str | None = None,
        chunk_id: int | None = None,
        event_bus: EventBus | None = None,
    ) -> Path:
        # Path safety: validate before worker call
        source_audio_path = Path(source_audio_path)
        reference_audio_path = Path(reference_audio_path)
        output_path = Path(output_path)

        if not source_audio_path.exists():
            raise FileNotFoundError(str(source_audio_path))
        if not reference_audio_path.exists():
            raise FileNotFoundError(str(reference_audio_path))

        # Always use absolute paths over IPC to avoid relative path bugs.
        src_abs = source_audio_path.resolve()
        ref_abs = reference_audio_path.resolve()
        out_abs = output_path.resolve()

        # Auto-start behavior + health validation
        self.start()
        assert self._client is not None

        self._maybe_recycle()

        logger.info("Speaker conversion started")
        settings_dict = dict(settings or {})
        diffusion_steps = int(settings_dict.get("diffusion_steps", 30))
        progress_adapter: VcProgressAdapter | None = None
        progress_bridge: VcProgressBridge | None = None
        if (
            event_bus is not None
            and project_id is not None
            and part_id is not None
            and chunk_id is not None
        ):
            settings_dict.setdefault("chunk_id", chunk_id)
            progress_adapter = VcProgressAdapter(
                project_id=project_id,
                part_id=part_id,
                event_bus=event_bus,
                total_steps=diffusion_steps,
            )
            progress_bridge = VcProgressBridge(progress_adapter)
            try:
                progress_adapter.start_chunk(chunk_id)
            except Exception:
                logger.warning("VC progress start_chunk failed", exc_info=True)

        try:
            payload = self._client.convert(
                source_audio_path=src_abs,
                reference_audio_path=ref_abs,
                output_path=out_abs,
                settings=settings_dict,
                job_id=None,
                on_progress=(
                    progress_bridge.on_progress_message
                    if progress_bridge is not None
                    else None
                ),
            )

            if not (isinstance(payload, dict) and payload.get("type") == "convert_completed"):
                if progress_adapter is not None:
                    try:
                        progress_adapter.fail_chunk(str(payload))
                    except Exception:
                        logger.warning("VC progress fail_chunk failed", exc_info=True)
                raise RuntimeError(f"Speaker conversion failed: {payload}")

            if not out_abs.exists():
                raise RuntimeError(
                    f"Speaker conversion completed but output file missing: {out_abs}"
                )

            if progress_adapter is not None:
                try:
                    progress_adapter.complete_chunk()
                except Exception:
                    logger.warning("VC progress complete_chunk failed", exc_info=True)
        except Exception as exc:
            if progress_adapter is not None and progress_adapter.session is not None:
                try:
                    progress_adapter.fail_chunk(str(exc))
                except Exception:
                    logger.warning("VC progress fail_chunk failed", exc_info=True)
            raise

        self._conversions_since_start += 1
        logger.info("Speaker conversion completed")
        return out_abs


def _default_storage_paths(project_root: Path) -> tuple[Path, Path, Path, Path]:
    storage_dir = project_root / "storage"
    return (
        storage_dir / "worker_source.wav",
        storage_dir / "worker_ref.wav",
        storage_dir / "service_out1.wav",
        storage_dir / "service_out2.wav",
    )


def _discover_narration_chunks(storage_dir: Path) -> list[Path]:
    # Real narration chunks expected as 0001.wav, 0002.wav, ...
    candidates = sorted(storage_dir.glob("[0-9][0-9][0-9][0-9].wav"))
    return [p for p in candidates if p.is_file()]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--real-proof",
            action="store_true",
            help="Convert first 5 narration chunks in storage/0001.wav... using worker service",
        )
        args = parser.parse_args()

        project_root = Path(__file__).resolve().parents[2]
        storage_dir = project_root / "storage"
        src, ref, out1, out2 = _default_storage_paths(project_root)

        svc = WorkerSpeakerService()
        print("service: starting (auto-start on first convert)")

        if args.real_proof:
            if not storage_dir.exists():
                raise FileNotFoundError(str(storage_dir))
            if not ref.exists():
                raise FileNotFoundError(str(ref))

            chunks = _discover_narration_chunks(storage_dir)
            if len(chunks) == 0:
                raise FileNotFoundError(
                    f"No narration chunks found in {storage_dir} matching 0001.wav, 0002.wav, ..."
                )

            chunks = chunks[:5]
            out_dir = storage_dir / "proof_outputs"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Proof-only recycle policy
            svc.max_conversions_per_worker = 3

            started = time.time()
            worker_recycles = 0
            successful = 0
            failed = 0
            last_pid: int | None = None

            print("service: health", json.dumps(svc.health(), indent=2, ensure_ascii=False))

            for chunk_path in chunks:
                name = chunk_path.name
                out_path = out_dir / name

                pid_before = svc._last_worker_pid
                try:
                    out = svc.convert_chunk(chunk_path, ref, out_path, settings=None)
                    if not out.exists() or out.stat().st_size <= 0:
                        raise RuntimeError(f"Output invalid for {name}: {out}")
                    successful += 1
                    print(f"[OK] chunk {name} converted")
                except Exception as e:
                    failed += 1
                    print(f"[FAIL] chunk {name} failed: {e}")

                pid_after = svc._last_worker_pid
                same_worker = (pid_before is not None) and (pid_before == pid_after)
                print(
                    f"worker_pid_before={pid_before} worker_pid_after={pid_after} same_worker={same_worker}"
                )

                if last_pid is not None and pid_after is not None and pid_after != last_pid:
                    worker_recycles += 1
                if pid_after is not None:
                    last_pid = pid_after

            elapsed = time.time() - started
            print(
                "summary:",
                f"total_chunks={len(chunks)}",
                f"successful_chunks={successful}",
                f"failed_chunks={failed}",
                f"worker_recycles={worker_recycles}",
                f"elapsed_seconds={elapsed:.2f}",
            )

            svc.shutdown()
            print("service: shutdown complete")
        else:
            # Convert twice sequentially.
            print("service: health", json.dumps(svc.health(), indent=2, ensure_ascii=False))
            pid_after_health = svc._last_worker_pid

            p1 = svc.convert_chunk(src, ref, out1, settings=None)
            pid_after_1 = svc._last_worker_pid
            print(f"service: convert1 ok -> {p1}")

            p2 = svc.convert_chunk(src, ref, out2, settings=None)
            pid_after_2 = svc._last_worker_pid
            print(f"service: convert2 ok -> {p2}")

            same_worker = (pid_after_health is not None) and (pid_after_health == pid_after_1 == pid_after_2)
            print(f"service: worker reused = {same_worker} (pid={pid_after_health})")

            svc.shutdown()
            print("service: shutdown complete")
    except Exception:
        traceback.print_exc()
        raise

