"""Gemini non-streaming TTS (migrated from prototypes/ai_studio_nonstream.py)."""

from __future__ import annotations

import logging
import mimetypes
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from google import genai
from google.genai import types

from backend.services.scene_context import SceneContext
from backend.services.token_pool import GenerationCancelled, TokenPool
from backend.services.tts_api_event_store import (
    extract_google_error_fields,
    extract_request_id,
    persist_tts_api_event,
)
from backend.services.tts_debug_store import (
    build_request_payload,
    build_response_payload,
    infer_tts_debug_context,
    persist_tts_debug_record,
    sanitize_config_snapshot,
    scene_context_block,
)

logger = logging.getLogger(__name__)

MODEL = "gemini-3.1-flash-tts-preview"

# Single narrator for all chunks — locked in speech_config (no multi-speaker).
NARRATOR_VOICE_NAME = "Sulafat"

# Phase T1: server deadline cap (ms) for fast token rotation after a transient failure on the chunk.
# HttpOptions.timeout is sent as X-Server-Timeout; Gemini enforces a 10s minimum deadline.
_TTS_FAIL_FAST_TIMEOUT_MS = 10_500

# After the first failing token on a chunk, fast-fail at most this many additional tokens
# before allowing a long generateContent attempt (success can take 60s+).
_TTS_FAIL_FAST_MAX_ADDITIONAL_TOKENS = 4

_DIRECTOR_PROMPT = """Read the following Persian audiobook narration.

# Director's note

Style:
Warm, emotionally engaging, cinematic, deeply human.

Voice:
Single narrator only — use prebuilt voice Sulafat for the entire audiobook.
Warm masculine Persian narrator.
Deep but soft voice.
Professional audiobook quality.
Natural Persian pronunciation.
Do not switch voices or introduce a second speaker.

Pacing:
Natural pacing.
Not too slow.
Not robotic.
Smooth storytelling rhythm.

Emotion:
Warm, reflective, emotionally engaging.
Speak naturally like a premium Persian audiobook narrator telling an important life story.

Avoid:
Monotone voice.
Cold documentary tone.
Excessive slowness.
Overly dramatic acting.

## Sample Context:
A premium Persian audiobook narrator telling an important life story in a warm, emotionally engaging, cinematic way. Natural pacing, warm emotional depth, human sounding voice.

## Transcript (single narrator — Sulafat):

Narration:
[speak warmly]
[natural pacing]
[cinematic]
[human tone]

"""


@dataclass
class TtsProgressHooks:
    on_calling: Callable[[], None] | None = None
    on_received: Callable[[], None] | None = None
    on_rate_limited: Callable[[int], None] | None = None
    on_waiting_tick: Callable[[int], None] | None = None
    cancel_checker: Callable[[], bool] | None = None
    # Observability only — does not affect token selection.
    on_token_used: Callable[[str], None] | None = None
    on_quota_exhausted: Callable[[str], None] | None = None
    on_transient_failure: Callable[[str], None] | None = None
    on_token_switched: Callable[[str, str, str], None] | None = None
    on_pool_waiting: Callable[[int], None] | None = None
    on_chunk_success: Callable[[str], None] | None = None


def _build_generate_config() -> types.GenerateContentConfig:
    """Single-speaker TTS config — same voice (Sulafat) on every chunk."""
    return types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=NARRATOR_VOICE_NAME,
                )
            ),
        ),
    )


def _iter_response_parts(response):
    if response is None:
        return
    parts = getattr(response, "parts", None)
    if parts:
        for part in parts:
            yield part
        return
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", None) or []:
            yield part


def _collect_inline_audio(response) -> list:
    items = []
    for part in _iter_response_parts(response):
        inline_data = getattr(part, "inline_data", None)
        if inline_data and getattr(inline_data, "data", None):
            items.append(inline_data)
    return items


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data


def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    bits_per_sample = 16
    rate = 24000
    for param in mime_type.split(";"):
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).upper()
    return "429" in message or "RESOURCE_EXHAUSTED" in message


def _is_fatal_tts_config_error(exc: Exception) -> bool:
    """
    Non-retryable client/config errors — abort the current chunk immediately.

    Do not rotate tokens, sleep/retry, or treat as transient failover.
    """
    message = str(exc)
    upper = message.upper()
    if "INVALID_ARGUMENT" not in upper and "400" not in message:
        return False
    lower = message.lower()
    return "deadline" in lower or "too short" in lower


def _is_transport_timeout_error(exc: Exception) -> bool:
    """HTTP/client timeouts — treat like other transient failover signals."""
    if isinstance(exc, TimeoutError):
        return True
    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.TimeoutException,
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ),
        ):
            return True
    except ImportError:
        pass
    message = str(exc).upper()
    return any(
        token in message
        for token in (
            "TIMEOUT",
            "TIMED OUT",
            "DEADLINE_EXCEEDED",
            "DEADLINE EXCEEDED",
        )
    )


def _is_transient_failover_error(exc: Exception) -> bool:
    """
    Errors that should trigger fast token failover for the current chunk.

    IMPORTANT: This is not a permanent quarantine. It only influences intra-chunk rotation.
    """
    if _is_fatal_tts_config_error(exc):
        return False
    if _is_transport_timeout_error(exc):
        return True
    message = str(exc).upper()
    return any(
        token in message
        for token in (
            "429",
            "RESOURCE_EXHAUSTED",
            "500",
            "503",
            "INTERNAL",
            "UNAVAILABLE",
        )
    )


def _should_use_fail_fast_http_timeout(
    failed_tokens_this_chunk: set[str],
) -> bool:
    """
    Use a short HTTP timeout only while rotating through likely-dead tokens.

    The first token on a chunk keeps the default (unlimited) timeout so healthy
    128s+ generations are not cut off. After the first transient failure, cap the
    next few failover attempts at the minimum server deadline (~10.5s), then allow
    a long attempt again so a working token late in the pool can still finish.
    """
    if not failed_tokens_this_chunk:
        return False
    return len(failed_tokens_this_chunk) <= _TTS_FAIL_FAST_MAX_ADDITIONAL_TOKENS


def _config_for_tts_request(
    base_config: types.GenerateContentConfig,
    *,
    fail_fast: bool,
) -> types.GenerateContentConfig:
    if not fail_fast:
        return base_config
    return base_config.model_copy(
        update={
            "http_options": types.HttpOptions(timeout=_TTS_FAIL_FAST_TIMEOUT_MS),
        },
    )


def _build_tts_prompt(
    transcript: str,
    continuity_note: str | None = None,
    scene_context: SceneContext | None = None,
) -> str:
    parts = [_DIRECTOR_PROMPT.rstrip()]
    note = (continuity_note or "").strip()
    if note:
        parts.append("\n\n## Voice continuity (do NOT read aloud):\n")
        parts.append(note)
    # Phase 5.2 A/B: enhanced prompt only when scene feature is explicitly enabled.
    use_enhanced_scene_prompt = bool(scene_context and scene_context.is_enabled())
    if use_enhanced_scene_prompt:
        block = scene_context.build_prompt_block()
        if block:
            parts.append("\n\n")
            parts.append(block)
    # Baseline path: director + continuity + transcript (no scene block).
    parts.append("\n\n")
    parts.append(transcript.strip())
    return "".join(parts)


def generate_audio(
    text: str,
    output_path: str,
    token_pool: TokenPool,
    *,
    max_attempts: int = 15,
    hooks: TtsProgressHooks | None = None,
    continuity_note: str | None = None,
    scene_context: SceneContext | None = None,
) -> None:
    """Generate one WAV file for a text chunk with token fallback on quota errors."""
    prompt = _build_tts_prompt(text, continuity_note, scene_context=scene_context)
    config = _build_generate_config()
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]

    intake_id, chunk_index = infer_tts_debug_context(output_path)
    scene_block = scene_context_block(scene_context)
    transcript = text.strip()
    config_snapshot = sanitize_config_snapshot(
        model=MODEL,
        voice_name=NARRATOR_VOICE_NAME,
        temperature=1,
    )

    last_error: Exception | None = None
    tried_all_tokens = False
    cancel_checker = hooks.cancel_checker if hooks else None
    failed_tokens_this_chunk: set[str] = set()

    def _persist_debug(
        *,
        success: bool,
        token_name: str,
        attempt: int,
        error: str | None = None,
        wav_path: str | None = None,
        wav_size_bytes: int | None = None,
        mime_type: str | None = None,
        audio_bytes: int | None = None,
    ) -> None:
        record = {
            "chunk_index": chunk_index,
            "intake_id": intake_id,
            "request": build_request_payload(
                chunk_index=chunk_index,
                prompt=prompt,
                transcript=transcript,
                continuity_note=continuity_note,
                scene_block=scene_block,
                token_name=token_name,
                attempt=attempt,
                config_snapshot=config_snapshot,
            ),
            "response": build_response_payload(
                success=success,
                error=error,
                wav_path=wav_path,
                wav_size_bytes=wav_size_bytes,
                mime_type=mime_type,
                audio_bytes=audio_bytes,
            ),
        }
        persist_tts_debug_record(intake_id, chunk_index, record)

    for attempt in range(max_attempts):
        if cancel_checker and cancel_checker():
            raise GenerationCancelled("Generation cancelled.")

        # Skip any tokens that already failed for this chunk (fast failover).
        # TokenPool itself stays unchanged; this is purely local state.
        skip_hops = 0
        while token_pool.total and token_pool.current_name() in failed_tokens_this_chunk:
            skip_hops += 1
            if not token_pool.advance():
                # Pool cycle exhausted; clear chunk-local failures after cooldown reset.
                if hooks and hooks.on_pool_waiting:
                    hooks.on_pool_waiting(token_pool.wait_seconds)
                if hooks and hooks.on_rate_limited:
                    hooks.on_rate_limited(token_pool.wait_seconds)
                token_pool.wait_and_reset(
                    cancel_checker=cancel_checker,
                    on_tick=hooks.on_waiting_tick if hooks else None,
                )
                tried_all_tokens = True
                failed_tokens_this_chunk.clear()
                break
            if skip_hops > token_pool.total:
                break

        token_name = token_pool.current_name()
        if hooks and hooks.on_token_used:
            hooks.on_token_used(token_name)

        api_key = token_pool.current_key()
        client = genai.Client(api_key=api_key)
        fail_fast = _should_use_fail_fast_http_timeout(failed_tokens_this_chunk)
        request_config = _config_for_tts_request(config, fail_fast=fail_fast)
        http_timeout_ms = _TTS_FAIL_FAST_TIMEOUT_MS if fail_fast else None
        try:
            if hooks and hooks.on_calling:
                hooks.on_calling()
            logger.info(
                "Calling Gemini TTS (token %s/%s, fail_fast=%s)",
                token_pool.current_index,
                token_pool.total,
                fail_fast,
            )

            api_started = time.perf_counter()
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=request_config,
                )
            except Exception as api_exc:
                elapsed_ms = (time.perf_counter() - api_started) * 1000.0
                status_code, google_status, google_message = extract_google_error_fields(api_exc)
                switch_reason: str | None = None
                if _is_transient_failover_error(api_exc):
                    switch_reason = (
                        "429_quota" if _is_rate_limit_error(api_exc) else "transient_error"
                    )
                persist_tts_api_event(
                    model=MODEL,
                    voice=NARRATOR_VOICE_NAME,
                    token_name=token_name,
                    attempt_number=attempt + 1,
                    text_length=len(prompt),
                    elapsed_ms=elapsed_ms,
                    success=False,
                    chunk_id=chunk_index,
                    intake_id=intake_id,
                    status_code=status_code,
                    google_error_status=google_status,
                    google_error_message=google_message,
                    token_switch_reason=switch_reason,
                    request_id=None,
                    exception=api_exc,
                    fail_fast=fail_fast,
                    http_timeout_ms=http_timeout_ms,
                )
                raise

            elapsed_ms = (time.perf_counter() - api_started) * 1000.0
            persist_tts_api_event(
                model=MODEL,
                voice=NARRATOR_VOICE_NAME,
                token_name=token_name,
                attempt_number=attempt + 1,
                text_length=len(prompt),
                elapsed_ms=elapsed_ms,
                success=True,
                chunk_id=chunk_index,
                intake_id=intake_id,
                status_code=200,
                request_id=extract_request_id(response),
                fail_fast=fail_fast,
                http_timeout_ms=http_timeout_ms,
            )

            if hooks and hooks.on_received:
                hooks.on_received()
            logger.info("Gemini response received")

            inline_items = _collect_inline_audio(response)
            if not inline_items:
                raise RuntimeError("No audio data in Gemini response.")

            mime_type = inline_items[0].mime_type or "audio/L16;rate=24000"
            combined = b"".join(item.data for item in inline_items if item.data)
            if not combined:
                raise RuntimeError("Audio response was empty.")

            data_buffer = combined
            if mimetypes.guess_extension(mime_type) != ".wav":
                data_buffer = convert_to_wav(combined, mime_type)

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data_buffer)
            wav_resolved = str(out.resolve())
            wav_size = out.stat().st_size
            logger.info("Saved wav: %s", out.name)
            _persist_debug(
                success=True,
                token_name=token_name,
                attempt=attempt + 1,
                wav_path=wav_resolved,
                wav_size_bytes=wav_size,
                mime_type=mime_type,
                audio_bytes=len(combined),
            )
            if hooks and hooks.on_chunk_success:
                hooks.on_chunk_success(token_name)
            return

        except GenerationCancelled:
            raise
        except Exception as exc:
            last_error = exc
            if _is_fatal_tts_config_error(exc):
                _persist_debug(
                    success=False,
                    token_name=token_name,
                    attempt=attempt + 1,
                    error=str(exc),
                    wav_path=str(Path(output_path).resolve()),
                )
                raise RuntimeError(f"TTS fatal config error for chunk: {exc}") from exc
            if _is_transient_failover_error(exc):
                exhausted_name = token_pool.current_name()
                failed_tokens_this_chunk.add(exhausted_name)

                if _is_rate_limit_error(exc):
                    if hooks and hooks.on_quota_exhausted:
                        hooks.on_quota_exhausted(exhausted_name)
                elif hooks and hooks.on_transient_failure:
                    hooks.on_transient_failure(exhausted_name)

                # Honest waiting: only signal rate-limited when we actually wait/reset.
                if not token_pool.advance():
                    if hooks and hooks.on_pool_waiting:
                        hooks.on_pool_waiting(token_pool.wait_seconds)
                    if hooks and hooks.on_rate_limited:
                        hooks.on_rate_limited(token_pool.wait_seconds)
                    token_pool.wait_and_reset(
                        cancel_checker=cancel_checker,
                        on_tick=hooks.on_waiting_tick if hooks else None,
                    )
                    tried_all_tokens = True
                    failed_tokens_this_chunk.clear()
                elif hooks and hooks.on_token_switched:
                    reason = "429_quota" if _is_rate_limit_error(exc) else "transient_error"
                    hooks.on_token_switched(
                        exhausted_name,
                        token_pool.current_name(),
                        reason,
                    )
                continue

            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            _persist_debug(
                success=False,
                token_name=token_name,
                attempt=attempt + 1,
                error=str(exc),
                wav_path=str(Path(output_path).resolve()),
            )
            raise

    detail = f"after {max_attempts} attempts"
    if tried_all_tokens:
        detail += " (all tokens exhausted)"
    _persist_debug(
        success=False,
        token_name=token_pool.current_name(),
        attempt=max_attempts,
        error=f"{detail}: {last_error}",
        wav_path=str(Path(output_path).resolve()),
    )
    raise RuntimeError(f"TTS generation failed {detail}: {last_error}")
