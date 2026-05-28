"""
Speaker engine service interface + Phase 2A headless proof.

This file intentionally contains the smallest possible headless proof that
`speaker-engine` can run without Gradio/UI:

    source wav + reference wav -> headless VC -> output wav

Constraints (per user request):
- do not touch narration-engine
- do not touch speaker-engine UI (`app_vc_v2.py`)
- do not modify model logic; only consume the headless API
- no orchestration, no pipeline, no batch, no state, no manifests
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.contracts.manifests import SpeakerChunk, SpeakerManifest


@dataclass(frozen=True, slots=True)
class SpeakerSettings:
    """Contract placeholder for speaker conversion settings (Phase 1)."""

    options: dict[str, Any] | None = None


class SpeakerService(Protocol):
    """
    Interface boundary for speaker-engine.

    Phase 2+ will implement these methods by calling speaker-engine core code
    (non-Gradio path) or exposing it via a service boundary. Phase 1 defines
    signatures only.
    """

    def convert_chunk(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        settings: SpeakerSettings | None = None,
    ) -> Path:
        raise NotImplementedError

    def convert_batch(
        self,
        source_chunks: list[SpeakerChunk],
        reference_audio_path: Path,
        settings: SpeakerSettings,
    ) -> list[SpeakerChunk]:
        raise NotImplementedError

    def build_manifest(self, project_id: str, reference_audio_path: Path | None = None) -> SpeakerManifest:
        raise NotImplementedError


class HeadlessSpeakerService:
    """
    Minimal headless proof implementation for Phase 2A.

    - Lazily loads V2 VoiceConversionWrapper once, then reuses it.
    - Calls `VoiceConversionWrapper.convert_voice_with_streaming(stream_output=False, for_gradio=False)`
      and consumes the generator to retrieve a single final `(sr, waveform)` pair.
    - Writes WAV to `output_path`.

    This is intentionally not a pipeline and does not implement batch, resume, or manifests.
    """

    _vc_wrapper = None
    _device = None
    _dtype = None

    def __init__(
        self,
        *,
        speaker_engine_root: Path | None = None,
        config_path: Path | None = None,
        compile: bool = False,
        ar_checkpoint_path: str | None = None,
        cfm_checkpoint_path: str | None = None,
    ) -> None:
        self._speaker_engine_root = speaker_engine_root
        self._config_path = config_path
        self._compile = compile
        self._ar_checkpoint_path = ar_checkpoint_path
        self._cfm_checkpoint_path = cfm_checkpoint_path

    @staticmethod
    def _resolve_speaker_engine_root(explicit: Path | None) -> Path:
        if explicit is not None:
            return explicit
        # Default: AminVC/speaker-engine relative to this file (AminVC/app/services/speaker_service.py)
        return Path(__file__).resolve().parents[2] / "speaker-engine"

    @classmethod
    def _ensure_loaded(cls, *, speaker_engine_root: Path, config_path: Path, compile: bool,
                       ar_checkpoint_path: str | None, cfm_checkpoint_path: str | None) -> None:
        if cls._vc_wrapper is not None:
            return

        import sys

        # Make speaker-engine importable without installing as a package.
        # This does not import any UI modules.
        root_str = str(speaker_engine_root.resolve())
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        # Device/dtype helpers live in speaker-engine.
        from modules.device_utils import resolve_device, infer_dtype, safe_module_to_device  # type: ignore

        import torch  # type: ignore
        import yaml  # type: ignore
        from hydra.utils import instantiate  # type: ignore
        from omegaconf import DictConfig  # type: ignore

        cls._device = resolve_device()
        cls._dtype = infer_dtype(cls._device)

        cfg = DictConfig(yaml.safe_load(Path(config_path).read_text(encoding="utf-8")))
        vc_wrapper = instantiate(cfg)
        vc_wrapper.load_checkpoints(
            ar_checkpoint_path=ar_checkpoint_path,
            cfm_checkpoint_path=cfm_checkpoint_path,
        )
        vc_wrapper = safe_module_to_device(vc_wrapper, cls._device)
        vc_wrapper.eval()
        vc_wrapper.setup_ar_caches(max_batch_size=1, max_seq_len=4096, dtype=cls._dtype, device=cls._device)

        if compile:
            torch._inductor.config.coordinate_descent_tuning = True
            torch._inductor.config.triton.unique_kernel_names = True
            if hasattr(torch._inductor.config, "fx_graph_cache"):
                torch._inductor.config.fx_graph_cache = True
            vc_wrapper.compile_ar()

        cls._vc_wrapper = vc_wrapper

    def convert_chunk(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        settings: SpeakerSettings | None = None,
    ) -> Path:
        speaker_root = self._resolve_speaker_engine_root(self._speaker_engine_root)
        cfg_path = self._config_path or (speaker_root / "configs" / "v2" / "vc_wrapper.yaml")

        self._ensure_loaded(
            speaker_engine_root=speaker_root,
            config_path=cfg_path,
            compile=self._compile,
            ar_checkpoint_path=self._ar_checkpoint_path,
            cfm_checkpoint_path=self._cfm_checkpoint_path,
        )

        # Extract supported settings (only those exposed by convert_voice_with_streaming).
        opts = (settings.options if settings and settings.options else {}) if settings is not None else {}
        diffusion_steps = int(opts.get("diffusion_steps", 30))
        length_adjust = float(opts.get("length_adjust", 1.0))
        intelligibility_cfg_rate = float(opts.get("intelligebility_cfg_rate", opts.get("intelligibility_cfg_rate", 0.7)))
        similarity_cfg_rate = float(opts.get("similarity_cfg_rate", 0.7))
        top_p = float(opts.get("top_p", 0.7))
        temperature = float(opts.get("temperature", 0.7))
        repetition_penalty = float(opts.get("repetition_penalty", 1.5))
        convert_style = bool(opts.get("convert_style", False))
        anonymization_only = bool(opts.get("anonymization_only", False))

        generator = self._vc_wrapper.convert_voice_with_streaming(  # type: ignore[union-attr]
            source_audio_path=str(source_audio_path),
            target_audio_path=str(reference_audio_path),
            diffusion_steps=diffusion_steps,
            length_adjust=length_adjust,
            intelligebility_cfg_rate=intelligibility_cfg_rate,
            similarity_cfg_rate=similarity_cfg_rate,
            top_p=top_p,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            convert_style=convert_style,
            anonymization_only=anonymization_only,
            device=self._device,
            dtype=self._dtype,
            stream_output=False,
            for_gradio=False,
        )

        final: tuple[int, Any] | None = None
        for _stream_bytes, full_audio in generator:
            if full_audio is not None:
                final = full_audio

        if final is None:
            raise RuntimeError("Speaker conversion produced no final audio output.")

        sr, waveform = final

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import soundfile as sf  # type: ignore

        sf.write(str(output_path), waveform, int(sr))
        return output_path

    def convert_batch(self, source_chunks: list[SpeakerChunk], reference_audio_path: Path, settings: SpeakerSettings) -> list[SpeakerChunk]:
        raise NotImplementedError

    def build_manifest(self, project_id: str, reference_audio_path: Path | None = None) -> SpeakerManifest:
        raise NotImplementedError

    @staticmethod
    def proof_example() -> "HeadlessSpeakerService":
        """
        Tiny manual proof entry: returns a service instance that can be called as:

            svc = HeadlessSpeakerService.proof_example()
            svc.convert_chunk(Path("source.wav"), Path("ref.wav"), Path("out.wav"))

        No CLI. No UI. No orchestration.
        """

        return HeadlessSpeakerService()

