"""
NarrationService: HTTP boundary to narration-engine (Phase 2B).

Scope:
- Local HTTP calls only (no imports from narration-engine/)
- upload PDF, start generation, poll status, discover chunk WAVs
- return contract `NarrationManifest`

Explicit non-goals:
- no orchestration, pipeline, merge, speaker, queue, resume, UI
"""

from __future__ import annotations

import json
import logging
import time
import traceback
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config.settings import AppSettings
from app.contracts.manifests import ChunkManifest, NarrationChunk, NarrationManifest
from app.services.narration_chunk_executor import (
    NarrationChunkExecutor,
    WaveNarrationChunkExecutor,
)


logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = frozenset({"completed", "failed", "error"})
_CHUNK_GLOB = "[0-9][0-9][0-9][0-9].wav"


@dataclass(slots=True)
class NarrationService:
    """
    Production-safe wrapper around narration-engine FastAPI (HTTP only).
    """

    settings: AppSettings = AppSettings()

    @property
    def _base_url(self) -> str:
        return self.settings.narration_base_url.rstrip("/")

    @property
    def _timeout(self) -> float:
        return float(self.settings.narration_timeout_seconds)

    @property
    def _poll_interval(self) -> float:
        return float(self.settings.narration_poll_interval_seconds)

    @property
    def _narration_audio_root(self) -> Path:
        # Chunk WAVs: narration-engine/storage/temp/audio/{intake_id}/0001.wav
        return (
            self.settings.project_root
            / "narration-engine"
            / "storage"
            / "temp"
            / "audio"
        )

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        multipart_file: Path | None = None,
        allow_not_found: bool = False,
    ) -> dict[str, Any] | None:
        url = self._url(path)
        headers: dict[str, str] = {}
        data: bytes | None = None

        if multipart_file is not None:
            data, content_type = _encode_multipart_pdf(multipart_file)
            headers["Content-Type"] = content_type
        elif json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body)
            except json.JSONDecodeError:
                detail = body
            if allow_not_found and exc.code == 404:
                detail_text = detail if isinstance(detail, str) else json.dumps(detail)
                if "No generation status found" in detail_text:
                    return None
            raise RuntimeError(
                f"Narration HTTP {exc.code} {method} {path}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Narration engine unreachable at {self._base_url}: {exc}"
            ) from exc

    def generate_chunk(
        self,
        *,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
        output_path: Path,
        executor: NarrationChunkExecutor | None = None,
    ) -> Path:
        """
        Generate narration audio for a single E0 chunk (E6 worker path).

        Worker jobs use GeminiNarrationChunkExecutor by default (E6.1). This helper
        keeps WaveNarrationChunkExecutor unless an executor is passed explicitly.
        """
        runner = executor or WaveNarrationChunkExecutor()
        return runner.generate_chunk(
            project_id=project_id,
            part_id=part_id,
            chunk=chunk,
            output_path=output_path,
        )

    def health(self) -> dict[str, Any]:
        """
        Verify narration-engine availability via GET /health.
        """
        try:
            payload = self._request("GET", "/health")
        except RuntimeError:
            return {"ready": False, "base_url": self._base_url}

        ready = isinstance(payload, dict) and payload.get("status") == "ok"
        return {"ready": ready, "base_url": self._base_url, "detail": payload}

    def generate_chunks(self, pdf_path: Path) -> NarrationManifest:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path.resolve()))

        # Step 2 — upload PDF
        upload = self._request(
            "POST",
            "/api/v1/pdf/upload",
            multipart_file=pdf_path.resolve(),
        )
        intake_id = upload.get("intake_id") if isinstance(upload, dict) else None
        if not intake_id:
            raise RuntimeError(f"Invalid PDF upload response (missing intake_id): {upload}")
        logger.info("Narration upload complete")
        print("Uploaded PDF")

        # Step 3 — start generation
        start = self._request("POST", f"/api/v1/pdf/{intake_id}/continue", json_body={})
        if not isinstance(start, dict) or start.get("intake_id") != intake_id:
            raise RuntimeError(f"Invalid generation start response: {start}")
        logger.info("Narration generation started")
        print("Generation started")

        # Step 4 — poll until terminal
        self._poll_until_terminal(intake_id)

        # Step 5 — discover chunk WAVs (not merged/final output)
        chunk_paths = self._discover_chunk_wavs(intake_id)
        if not chunk_paths:
            raise RuntimeError(
                f"No narration chunk WAVs found for intake {intake_id} under "
                f"{self._narration_audio_root / intake_id}"
            )

        chunks = [
            NarrationChunk(
                chunk_id=int(p.stem),
                text="",
                tts_audio_path=p.resolve(),
            )
            for p in chunk_paths
        ]

        return NarrationManifest(
            project_id=intake_id,
            intake_id=intake_id,
            chunk_audio_paths=[c.tts_audio_path for c in chunks if c.tts_audio_path],
            metadata={"chunks": [{"chunk_id": c.chunk_id, "tts_audio_path": str(c.tts_audio_path)} for c in chunks]},
        )

    def _poll_until_terminal(self, intake_id: str) -> None:
        """
        Poll generation status until a terminal state.

        narration-engine writes status asynchronously after POST /continue
        (BackgroundTasks). A 404 "No generation status found" means the status
        file is not created yet — same intake_id, not a different generation id.
        """
        path = f"/api/v1/pdf/{intake_id}/generation/status"
        status_missing_polls = 0
        max_status_missing_polls = max(30, int(120 / self._poll_interval))

        while True:
            status = self._request("GET", path, allow_not_found=True)
            if status is None:
                status_missing_polls += 1
                if status_missing_polls > max_status_missing_polls:
                    raise RuntimeError(
                        "Generation status never appeared for "
                        f"intake_id={intake_id} (polled {path})"
                    )
                time.sleep(self._poll_interval)
                continue

            status_missing_polls = 0
            state = str(status.get("status", "")).lower()
            current = int(status.get("current_chunk") or 0)
            total = int(status.get("total_chunks") or 0)
            if total > 0:
                logger.info("Narration progress: %s/%s", current, total)
                print(f"Progress: {current}/{total}")

            if state in _TERMINAL_STATUSES:
                if state == "completed":
                    logger.info("Narration completed")
                    print("Completed")
                    return
                error = status.get("error") or status.get("status_label") or state
                raise RuntimeError(f"Narration generation failed ({state}): {error}")

            time.sleep(self._poll_interval)

    def _discover_chunk_wavs(self, intake_id: str) -> list[Path]:
        audio_dir = self._narration_audio_root / intake_id
        if not audio_dir.is_dir():
            return []

        paths = sorted(audio_dir.glob(_CHUNK_GLOB))
        # Ignore any non-chunk artifacts; chunk files are ####.wav only.
        valid = [p for p in paths if p.is_file() and p.stat().st_size > 0]
        return valid


def _encode_multipart_pdf(pdf_path: Path) -> tuple[bytes, str]:
    boundary = f"----AminVC{uuid.uuid4().hex}"
    filename = pdf_path.name
    file_data = pdf_path.read_bytes()

    parts: list[bytes] = []
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(file_data)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        project_root = AppSettings().project_root
        pdf_path = project_root / "storage" / "input" / "test.pdf"

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"Proof PDF missing: {pdf_path}. Place a PDF at storage/input/test.pdf"
            )

        svc = NarrationService()
        health = svc.health()
        if not health.get("ready"):
            raise RuntimeError(f"Narration service not healthy: {health}")
        print("Narration service healthy")

        manifest = svc.generate_chunks(pdf_path)
        print(f"Chunks found: {len(manifest.chunk_audio_paths)}")
        for path in manifest.chunk_audio_paths:
            print(path.name)
    except Exception:
        traceback.print_exc()
        raise
