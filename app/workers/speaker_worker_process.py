"""
Speaker worker subprocess (Phase 2A proof-of-stability).

Strict scope:
- persistent process
- loads speaker-engine model once
- sequential headless conversions via JSONL stdin/stdout
- writes WAV outputs

Hard rules:
- do not modify speaker-engine model logic
- do not use Gradio / UI modules
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import warnings
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from app.contracts.worker_messages import (
    ConvertCompletedResponse,
    ConvertRequest,
    ErrorResponse,
    HealthResponse,
    InitRequest,
    ProgressResponse,
    ReadyResponse,
    ShutdownCompleteResponse,
    ShutdownRequest,
    HealthRequest,
    parse_request,
    to_json_dict,
)


def _write_jsonl(message: Any) -> None:
    sys.stdout.write(json.dumps(to_json_dict(message), ensure_ascii=False) + "\n")
    sys.stdout.flush()


class SpeakerWorker:
    def __init__(self) -> None:
        self._ready = False
        self._device_str = "cpu"
        self._sr: int | None = None
        self._vc_wrapper = None
        self._device = None
        self._dtype = None
        self._torch_available: bool = False
        self._torch_version: str | None = None

    @staticmethod
    def _speaker_engine_root() -> Path:
        # AminVC/app/workers/speaker_worker_process.py -> AminVC/
        return Path(__file__).resolve().parents[2] / "speaker-engine"

    def init(self) -> None:
        if self._ready:
            return

        # CPU-first safety: allow override by env, but default to CPU.
        os.environ.setdefault("FORCE_CPU", "1")

        speaker_root = self._speaker_engine_root().resolve()
        os.chdir(str(speaker_root))

        # Make speaker-engine importable as top-level modules (modules.*, hf_utils, etc.)
        root_str = str(speaker_root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        # Silence known noisy warning that can break JSONL stdout if emitted during imports.
        warnings.filterwarnings(
            "ignore",
            message=r".*weight_norm.*deprecated.*",
            category=FutureWarning,
        )

        # Redirect any startup prints/warnings/logging produced by imports/model loading to stderr.
        # Stdout must remain JSONL-only for the protocol.
        with redirect_stdout(sys.stderr):
            from modules.device_utils import (  # type: ignore
                resolve_device,
                infer_dtype,
                safe_module_to_device,
            )

            import torch  # type: ignore
            import yaml  # type: ignore
            from hydra.utils import instantiate  # type: ignore
            from omegaconf import DictConfig  # type: ignore

        # Record interpreter torch availability/version for diagnostics.
        # This must not affect model behavior.
        try:
            import torch as _torch  # type: ignore

            self._torch_available = True
            self._torch_version = getattr(_torch, "__version__", None)
        except Exception:
            self._torch_available = False
            self._torch_version = None

        self._device = resolve_device()
        self._dtype = infer_dtype(self._device)
        self._device_str = str(self._device.type)

        with redirect_stdout(sys.stderr):
            cfg_path = speaker_root / "configs" / "v2" / "vc_wrapper.yaml"
            cfg = DictConfig(yaml.safe_load(cfg_path.read_text(encoding="utf-8")))
            vc_wrapper = instantiate(cfg)
            vc_wrapper.load_checkpoints()
            vc_wrapper = safe_module_to_device(vc_wrapper, self._device)
            vc_wrapper.eval()
            vc_wrapper.setup_ar_caches(
                max_batch_size=1,
                max_seq_len=4096,
                dtype=self._dtype,
                device=self._device,
            )

        # Record SR for health reporting.
        self._sr = int(getattr(vc_wrapper, "sr", 0) or 0) or None

        self._vc_wrapper = vc_wrapper
        self._ready = True

    def handle_init(self, _req: InitRequest) -> ReadyResponse:
        self.init()
        return ReadyResponse(ready=True, device=self._device_str, sr=self._sr)

    def handle_health(self, _req: HealthRequest) -> HealthResponse:
        return HealthResponse(ready=self._ready, device=self._device_str, sr=self._sr)

    def handle_convert(self, req: ConvertRequest) -> ConvertCompletedResponse:
        if not self._ready:
            self.init()

        assert self._vc_wrapper is not None

        source = req.source_audio_path
        reference = req.reference_audio_path
        output = Path(req.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Settings are pass-through placeholders; only known keys are forwarded.
        s = req.settings or {}
        diffusion_steps = int(s.get("diffusion_steps", 30))
        chunk_id = int(s.get("chunk_id", 0))
        last_progress_key: tuple[int, int, int, int] | None = None

        def progress_callback(
            current_step: int,
            total_steps: int,
            segment_index: int = 0,
            segment_total: int = 0,
        ) -> None:
            nonlocal last_progress_key
            key = (current_step, total_steps, segment_index, segment_total)
            if key == last_progress_key:
                return
            last_progress_key = key
            try:
                _write_jsonl(
                    ProgressResponse(
                        chunk_id=chunk_id,
                        current_step=current_step,
                        total_steps=total_steps,
                        segment_index=segment_index,
                        segment_total=segment_total,
                    )
                )
            except Exception:
                pass

        generator = self._vc_wrapper.convert_voice_with_streaming(  # type: ignore[union-attr]
            source_audio_path=source,
            target_audio_path=reference,
            diffusion_steps=diffusion_steps,
            length_adjust=float(s.get("length_adjust", 1.0)),
            intelligebility_cfg_rate=float(s.get("intelligebility_cfg_rate", 0.7)),
            similarity_cfg_rate=float(s.get("similarity_cfg_rate", 0.7)),
            top_p=float(s.get("top_p", 0.7)),
            temperature=float(s.get("temperature", 0.7)),
            repetition_penalty=float(s.get("repetition_penalty", 1.5)),
            convert_style=bool(s.get("convert_style", False)),
            anonymization_only=bool(s.get("anonymization_only", False)),
            device=self._device,
            dtype=self._dtype,
            stream_output=False,
            for_gradio=False,
            progress_callback=progress_callback,
        )

        final: tuple[int, Any] | None = None
        for _stream_bytes, full_audio in generator:
            if full_audio is not None:
                final = full_audio

        if final is None:
            raise RuntimeError("Conversion produced no final audio.")

        sr, waveform = final

        import soundfile as sf  # type: ignore

        sf.write(str(output), waveform, int(sr))
        return ConvertCompletedResponse(job_id=req.job_id, output_path=str(output))

    def handle_shutdown(self, _req: ShutdownRequest) -> ShutdownCompleteResponse:
        return ShutdownCompleteResponse()


def main() -> None:
    worker = SpeakerWorker()

    # Attempt eager init so READY is emitted immediately.
    try:
        worker.init()
        # READY must be strict JSONL on stdout. Include interpreter diagnostics.
        _write_jsonl(
            {
                "type": "ready",
                "ready": True,
                "device": worker._device_str,
                "sr": worker._sr,
                "python_executable": sys.executable,
                "python_version": sys.version,
                "cwd": os.getcwd(),
                "torch_available": worker._torch_available,
                "torch_version": worker._torch_version,
            }
        )
    except Exception as exc:
        _write_jsonl(
            ErrorResponse(
                message="Worker failed during startup init",
                detail={
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "python_executable": sys.executable,
                    "python_version": sys.version,
                    "cwd": os.getcwd(),
                    "sys_path_first10": sys.path[:10],
                },
            )
        )
        return

    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
            req = parse_request(payload)

            if isinstance(req, InitRequest):
                _write_jsonl(worker.handle_init(req))
                continue
            if isinstance(req, HealthRequest):
                _write_jsonl(worker.handle_health(req))
                continue
            if isinstance(req, ConvertRequest):
                _write_jsonl(worker.handle_convert(req))
                continue
            if isinstance(req, ShutdownRequest):
                # Respond first, then exit.
                _write_jsonl(worker.handle_shutdown(req))
                return

            _write_jsonl(ErrorResponse(message="Unhandled request type", detail=payload))
        except Exception as exc:
            _write_jsonl(
                ErrorResponse(
                    job_id=(payload.get("job_id") if isinstance(payload, dict) else None),  # type: ignore[name-defined]
                    message="Worker error handling request",
                    detail={"error": str(exc), "traceback": traceback.format_exc()},
                )
            )


if __name__ == "__main__":
    main()

