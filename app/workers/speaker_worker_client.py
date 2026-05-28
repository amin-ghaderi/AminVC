"""
Speaker worker client (Phase 2A proof).

Strict scope:
- subprocess.Popen with stdin/stdout pipes
- JSONL requests/responses
- start/health/convert/shutdown methods
- minimal proof() helper (start -> health -> convert twice -> shutdown)
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import traceback
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config.settings import AppSettings
from app.contracts.worker_messages import (
    ConvertCompletedResponse,
    ConvertRequest,
    ErrorResponse,
    HealthRequest,
    HealthResponse,
    InitRequest,
    ShutdownRequest,
    to_json_dict,
)


@dataclass(slots=True)
class SpeakerWorkerClient:
    python_executable: str = AppSettings().speaker_python_executable
    project_root: Path = Path(__file__).resolve().parents[2]
    process: subprocess.Popen[str] | None = None
    _stderr_tail: deque[str] = field(default_factory=lambda: deque(maxlen=50))
    _stderr_thread: threading.Thread | None = None

    def _worker_module(self) -> str:
        return "app.workers.speaker_worker_process"

    def _start_stderr_drain(self) -> None:
        if not self.process or not self.process.stderr:
            return
        if self._stderr_thread and self._stderr_thread.is_alive():
            return

        def _drain() -> None:
            assert self.process is not None and self.process.stderr is not None
            for line in self.process.stderr:
                text = (line or "").rstrip("\n")
                if text:
                    self._stderr_tail.append(text)

        self._stderr_thread = threading.Thread(target=_drain, daemon=True)
        self._stderr_thread.start()

    def start(self) -> dict[str, Any]:
        if self.process is not None and self.process.poll() is None:
            return {"started": True, "already_running": True}

        exe = Path(self.python_executable)
        if not exe.exists():
            raise RuntimeError(
                f"Speaker worker python executable not found: {self.python_executable}"
            )

        self.process = subprocess.Popen(
            [self.python_executable, "-m", self._worker_module()],
            cwd=str(self.project_root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        self._start_stderr_drain()

        # Read first line: READY or ERROR
        first = self._read_line()
        if isinstance(first, dict) and first.get("type") in ("error", "non_json_output"):
            # Enrich startup failures with recent stderr tail (logs/warnings).
            first.setdefault("detail", {})
            if isinstance(first.get("detail"), dict):
                first["detail"]["stderr_tail"] = list(self._stderr_tail)
        # Return the exact interpreter path used for deterministic debugging.
        return {"started": True, "python_executable_used": self.python_executable, "first_message": first}

    def _write(self, message: Any) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("Worker process is not started.")
        self.process.stdin.write(json.dumps(to_json_dict(message), ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def _read_line(self) -> dict[str, Any]:
        if not self.process or not self.process.stdout:
            raise RuntimeError("Worker process is not started.")
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError(
                    "Worker process produced no output (terminated?). "
                    f"stderr_tail={list(self._stderr_tail)}"
                )
            if not line.strip():
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # Surface non-JSON output as an ERROR-shaped dict for debugging.
                return {
                    "type": "error",
                    "message": "non_json_output",
                    "detail": {
                        "stdout_line": line.rstrip("\n"),
                        "stderr_tail": list(self._stderr_tail),
                    },
                }

    def _request(self, message: Any) -> dict[str, Any]:
        self._write(message)
        return self._read_line()

    def health(self) -> dict[str, Any]:
        return self._request(HealthRequest())

    def init(self) -> dict[str, Any]:
        return self._request(InitRequest())

    def convert(
        self,
        *,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        settings: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        msg = ConvertRequest(
            job_id=job_id or str(uuid.uuid4()),
            source_audio_path=str(source_audio_path),
            reference_audio_path=str(reference_audio_path),
            output_path=str(output_path),
            settings=settings or {},
        )
        return self._request(msg)

    def shutdown(self) -> dict[str, Any]:
        try:
            resp = self._request(ShutdownRequest())
        finally:
            if self.process is not None:
                self.process.wait(timeout=10)
        return resp

    @staticmethod
    def proof(
        *,
        python_executable: str = AppSettings().speaker_python_executable,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path_1: Path,
        output_path_2: Path,
    ) -> dict[str, Any]:
        """
        Minimal proof function:
        1) start worker
        2) health()
        3) convert same inputs twice
        4) shutdown
        """

        client = SpeakerWorkerClient(python_executable=python_executable)
        result: dict[str, Any] = {"start": None, "health": None, "convert1": None, "convert2": None, "shutdown": None}
        result["start"] = client.start()
        first = (result["start"] or {}).get("first_message") if isinstance(result["start"], dict) else None
        if isinstance(first, dict) and first.get("type") == "error":
            # Worker failed during startup init (dependency/cwd issues). Return early.
            return result

        result["health"] = client.health()
        result["convert1"] = client.convert(
            source_audio_path=source_audio_path,
            reference_audio_path=reference_audio_path,
            output_path=output_path_1,
            settings={},
            job_id="proof-1",
        )
        result["convert2"] = client.convert(
            source_audio_path=source_audio_path,
            reference_audio_path=reference_audio_path,
            output_path=output_path_2,
            settings={},
            job_id="proof-2",
        )
        result["shutdown"] = client.shutdown()
        return result


def _default_storage_paths(project_root: Path) -> tuple[Path, Path, Path, Path]:
    storage_dir = project_root / "storage"
    return (
        storage_dir / "worker_source.wav",
        storage_dir / "worker_ref.wav",
        storage_dir / "worker_out1.wav",
        storage_dir / "worker_out2.wav",
    )


if __name__ == "__main__":
    try:
        settings = AppSettings()
        project_root = Path(__file__).resolve().parents[2]
        src, ref, out1, out2 = _default_storage_paths(project_root)

        result = SpeakerWorkerClient.proof(
            python_executable=settings.speaker_python_executable,
            source_audio_path=src,
            reference_audio_path=ref,
            output_path_1=out1,
            output_path_2=out2,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception:
        traceback.print_exc()
        raise
