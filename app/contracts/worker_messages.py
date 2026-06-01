"""
JSONL IPC message contracts for AminVC speaker worker (Phase 2A proof).

Strict scope:
- schemas only (dataclasses + helpers)
- no worker implementation
- newline-delimited JSON messages over stdin/stdout
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TypedDict, cast


# -------------------------
# Message type literals
# -------------------------

RequestType = Literal["init", "convert", "health", "shutdown"]
ResponseType = Literal[
    "ready",
    "progress",
    "convert_completed",
    "health_response",
    "error",
    "shutdown_complete",
]


class JsonDict(TypedDict, total=False):
    type: str
    job_id: str
    message: str
    detail: Any


@dataclass(frozen=True, slots=True)
class InitRequest:
    type: Literal["init"] = "init"


@dataclass(frozen=True, slots=True)
class HealthRequest:
    type: Literal["health"] = "health"


@dataclass(frozen=True, slots=True)
class ShutdownRequest:
    type: Literal["shutdown"] = "shutdown"


@dataclass(frozen=True, slots=True)
class ConvertRequest:
    type: Literal["convert"] = "convert"
    job_id: str = ""
    source_audio_path: str = ""
    reference_audio_path: str = ""
    output_path: str = ""
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReadyResponse:
    type: Literal["ready"] = "ready"
    ready: bool = True
    device: str = "cpu"
    sr: int | None = None


@dataclass(frozen=True, slots=True)
class HealthResponse:
    type: Literal["health_response"] = "health_response"
    ready: bool = True
    device: str = "cpu"
    sr: int | None = None


@dataclass(frozen=True, slots=True)
class ProgressResponse:
    type: Literal["progress"] = "progress"
    chunk_id: int = 0
    current_step: int = 0
    total_steps: int = 0


@dataclass(frozen=True, slots=True)
class ConvertCompletedResponse:
    type: Literal["convert_completed"] = "convert_completed"
    job_id: str = ""
    output_path: str = ""


@dataclass(frozen=True, slots=True)
class ShutdownCompleteResponse:
    type: Literal["shutdown_complete"] = "shutdown_complete"


@dataclass(frozen=True, slots=True)
class ErrorResponse:
    type: Literal["error"] = "error"
    job_id: str | None = None
    message: str = "Worker error"
    detail: Any | None = None


def to_json_dict(obj: Any) -> dict[str, Any]:
    """
    Convert a request/response dataclass into a JSON-serializable dict.
    """

    if hasattr(obj, "__dataclass_fields__"):
        return cast(dict[str, Any], asdict(obj))
    if isinstance(obj, dict):
        return cast(dict[str, Any], obj)
    raise TypeError(f"Unsupported message type: {type(obj)}")


def parse_request(payload: dict[str, Any]) -> InitRequest | HealthRequest | ShutdownRequest | ConvertRequest:
    """
    Parse a request dict into one of the request dataclasses.
    Raises ValueError on unknown types.
    """

    msg_type = payload.get("type")
    if msg_type == "init":
        return InitRequest()
    if msg_type == "health":
        return HealthRequest()
    if msg_type == "shutdown":
        return ShutdownRequest()
    if msg_type == "convert":
        return ConvertRequest(
            job_id=str(payload.get("job_id") or ""),
            source_audio_path=str(payload.get("source_audio_path") or ""),
            reference_audio_path=str(payload.get("reference_audio_path") or ""),
            output_path=str(payload.get("output_path") or ""),
            settings=cast(dict[str, Any], payload.get("settings") or {}),
        )
    raise ValueError(f"Unknown request type: {msg_type!r}")


def parse_progress(payload: dict[str, Any]) -> ProgressResponse:
    return ProgressResponse(
        chunk_id=int(payload.get("chunk_id", 0)),
        current_step=int(payload.get("current_step", 0)),
        total_steps=int(payload.get("total_steps", 0)),
    )


def is_terminal_response(payload: dict[str, Any]) -> bool:
    msg_type = payload.get("type")
    return msg_type in ("convert_completed", "error", "shutdown_complete")

