"""E5.2 — Speaker engine progress integration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.contracts.events import (
    EVENT_VC_CHUNK_COMPLETED,
    EVENT_VC_CHUNK_FAILED,
    EVENT_VC_CHUNK_STARTED,
    EVENT_VC_PROGRESS,
    EventEnvelope,
)
from app.contracts.worker_messages import ProgressResponse, parse_progress
from app.events.bus import EventBus
from app.vc.bridge import VcProgressBridge
from app.vc.progress_adapter import VcProgressAdapter
from app.workers.speaker_worker_client import SpeakerWorkerClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEAKER_ENGINE_ROOT = PROJECT_ROOT / "speaker-engine"


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


def _collect_vc(bus: EventBus) -> list[EventEnvelope]:
    received: list[EventEnvelope] = []
    for event_type in (
        EVENT_VC_CHUNK_STARTED,
        EVENT_VC_PROGRESS,
        EVENT_VC_CHUNK_COMPLETED,
        EVENT_VC_CHUNK_FAILED,
    ):
        bus.subscribe(event_type, received.append)
    return received


def test_cfm_progress_callback_invocation() -> None:
    pytest.importorskip("torch")
    if str(SPEAKER_ENGINE_ROOT) not in sys.path:
        sys.path.insert(0, str(SPEAKER_ENGINE_ROOT))

    from modules.v2.cfm import CFM  # type: ignore[import-not-found]

    import torch

    estimator = MagicMock()
    estimator.in_channels = 4
    cfm = CFM(estimator)
    device = torch.device("cpu")
    x = torch.zeros(1, 4, 8, device=device)
    x_lens = torch.LongTensor([8])
    prompt = torch.zeros(1, 4, 2, device=device)
    mu = torch.zeros(1, 4, 8, device=device)
    style = torch.zeros(1, 4, device=device)
    t_span = torch.linspace(0, 1, 4, device=device)

    calls: list[tuple[int, int]] = []

    def callback(current_step: int, total_steps: int) -> None:
        calls.append((current_step, total_steps))

    cfm.solve_euler(
        x,
        x_lens,
        prompt,
        mu,
        style,
        t_span,
        inference_cfg_rate=[0.0, 0.0],
        progress_callback=callback,
    )
    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_cfm_no_callback_compatibility() -> None:
    pytest.importorskip("torch")
    if str(SPEAKER_ENGINE_ROOT) not in sys.path:
        sys.path.insert(0, str(SPEAKER_ENGINE_ROOT))

    from modules.v2.cfm import CFM  # type: ignore[import-not-found]

    import torch

    estimator = MagicMock()
    estimator.in_channels = 4
    cfm = CFM(estimator)
    device = torch.device("cpu")
    x = torch.zeros(1, 4, 4, device=device)
    x_lens = torch.LongTensor([4])
    prompt = torch.zeros(1, 4, 1, device=device)
    mu = torch.zeros(1, 4, 4, device=device)
    style = torch.zeros(1, 4, device=device)

    out = cfm.inference(mu, x_lens, prompt, style, n_timesteps=2, inference_cfg_rate=[0.0, 0.0])
    assert out.shape == x.shape


def test_worker_progress_message_emission() -> None:
    messages: list[dict[str, Any]] = []

    def capture(message: Any) -> None:
        if hasattr(message, "__dataclass_fields__"):
            from app.contracts.worker_messages import to_json_dict

            messages.append(to_json_dict(message))
        else:
            messages.append(message)

    last_step = 0

    def progress_callback(current_step: int, total_steps: int) -> None:
        nonlocal last_step
        if current_step == last_step:
            return
        last_step = current_step
        capture(
            ProgressResponse(
                chunk_id=17,
                current_step=current_step,
                total_steps=total_steps,
            )
        )

    progress_callback(1, 30)
    progress_callback(1, 30)
    progress_callback(2, 30)

    assert len(messages) == 2
    assert messages[0] == {
        "type": "progress",
        "chunk_id": 17,
        "current_step": 1,
        "total_steps": 30,
        "segment_index": 0,
        "segment_total": 0,
    }


def test_main_process_progress_handling() -> None:
    client = SpeakerWorkerClient.__new__(SpeakerWorkerClient)
    client.process = MagicMock()
    client._stderr_tail = __import__("collections").deque(maxlen=50)

    lines = [
        json.dumps(
            {
                "type": "progress",
                "chunk_id": 5,
                "current_step": 1,
                "total_steps": 10,
            }
        )
        + "\n",
        json.dumps({"type": "convert_completed", "job_id": "j1", "output_path": "/out.wav"})
        + "\n",
    ]
    client.process.stdout.readline = MagicMock(side_effect=lines)
    client.process.stdin = MagicMock()
    client.process.stdin.write = MagicMock()
    client.process.stdin.flush = MagicMock()

    seen: list[ProgressResponse] = []

    result = client._request_convert(
        __import__("app.contracts.worker_messages", fromlist=["ConvertRequest"]).ConvertRequest(
            job_id="j1",
            source_audio_path="/a.wav",
            reference_audio_path="/b.wav",
            output_path="/out.wav",
        ),
        on_progress=seen.append,
    )

    assert len(seen) == 1
    assert seen[0].current_step == 1
    assert result["type"] == "convert_completed"


def test_adapter_lifecycle(event_bus: EventBus) -> None:
    received = _collect_vc(event_bus)
    adapter = VcProgressAdapter(
        project_id="book-1",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=5,
    )
    bridge = VcProgressBridge(adapter)
    adapter.start_chunk(17)
    for step in (1, 2, 3, 4, 5):
        bridge.on_progress_message(
            {"type": "progress", "chunk_id": 17, "current_step": step, "total_steps": 5}
        )
    adapter.complete_chunk()

    types = [e.event_type for e in received]
    assert types[0] == EVENT_VC_CHUNK_STARTED
    assert types.count(EVENT_VC_PROGRESS) == 5
    assert types[-1] == EVENT_VC_CHUNK_COMPLETED
    progress_steps = [
        int(e.payload["current_step"])
        for e in received
        if e.event_type == EVENT_VC_PROGRESS
    ]
    assert progress_steps == [1, 2, 3, 4, 5]


def test_event_ordering_success(event_bus: EventBus) -> None:
    received = _collect_vc(event_bus)
    adapter = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=3,
    )
    bridge = VcProgressBridge(adapter)
    adapter.start_chunk(1)
    bridge.on_progress_message({"type": "progress", "chunk_id": 1, "current_step": 1, "total_steps": 3})
    bridge.on_progress_message({"type": "progress", "chunk_id": 1, "current_step": 2, "total_steps": 3})
    adapter.complete_chunk()
    types = [e.event_type for e in received]
    assert types == [
        EVENT_VC_CHUNK_STARTED,
        EVENT_VC_PROGRESS,
        EVENT_VC_PROGRESS,
        EVENT_VC_CHUNK_COMPLETED,
    ]


def test_event_ordering_failure(event_bus: EventBus) -> None:
    received = _collect_vc(event_bus)
    adapter = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=3,
    )
    bridge = VcProgressBridge(adapter)
    adapter.start_chunk(1)
    bridge.on_progress_message({"type": "progress", "chunk_id": 1, "current_step": 1, "total_steps": 3})
    adapter.fail_chunk("cuda oom")
    types = [e.event_type for e in received]
    assert types[-1] == EVENT_VC_CHUNK_FAILED


def test_bridge_failure_isolation(event_bus: EventBus) -> None:
    adapter = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=30,
    )
    adapter.start_chunk(1)
    bridge = VcProgressBridge(adapter)

    with patch.object(adapter, "update_progress", side_effect=RuntimeError("adapter down")):
        bridge.on_progress_message(
            {
                "type": "progress",
                "chunk_id": 1,
                "current_step": 2,
                "total_steps": 30,
                "segment_index": 1,
                "segment_total": 2,
            }
        )
    assert adapter.session is not None


def test_diffusion_steps_propagation(event_bus: EventBus) -> None:
    received = _collect_vc(event_bus)
    adapter = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=25,
    )
    adapter.start_chunk(9)
    adapter.update_step(1)
    progress = [e for e in received if e.event_type == EVENT_VC_PROGRESS][0]
    assert progress.payload["total_steps"] == 25


def test_no_duplicate_step_events_bridge() -> None:
    adapter = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=None,
        total_steps=30,
    )
    adapter.start_chunk(1)
    bridge = VcProgressBridge(adapter)
    msg = {"type": "progress", "chunk_id": 1, "current_step": 7, "total_steps": 30}
    bridge.on_progress_message(msg)
    bridge.on_progress_message(msg)
    assert adapter.session is not None
    assert adapter.session.current_step == 7


def test_parse_progress_schema() -> None:
    progress = parse_progress(
        {
            "type": "progress",
            "chunk_id": 17,
            "current_step": 12,
            "total_steps": 30,
            "segment_index": 2,
            "segment_total": 5,
        }
    )
    assert progress.chunk_id == 17
    assert progress.current_step == 12
    assert progress.segment_index == 2
    assert progress.segment_total == 5


@pytest.mark.integration
def test_real_conversion_smoke_if_harness_available(tmp_path: Path) -> None:
    """Optional smoke: requires worker WAV fixtures under storage/."""
    storage = PROJECT_ROOT / "storage"
    src = storage / "worker_source.wav"
    ref = storage / "worker_ref.wav"
    if not src.is_file() or not ref.is_file():
        pytest.skip("worker_source.wav / worker_ref.wav not present")

    from app.services.speaker_service import WorkerSpeakerService

    bus = EventBus()
    received = _collect_vc(bus)
    out = tmp_path / "vc_out.wav"
    svc = WorkerSpeakerService()
    try:
        svc.convert_chunk(
            src,
            ref,
            out,
            settings={"diffusion_steps": 4},
            project_id="audit-book",
            part_id="part-001",
            chunk_id=1,
            event_bus=bus,
        )
    finally:
        svc.shutdown()

    assert out.is_file()
    progress_events = [e for e in received if e.event_type == EVENT_VC_PROGRESS]
    assert EVENT_VC_CHUNK_STARTED in [e.event_type for e in received]
    assert EVENT_VC_CHUNK_COMPLETED in [e.event_type for e in received]
    assert len(progress_events) >= 1
    steps = [int(e.payload["current_step"]) for e in progress_events]
    assert steps == sorted(steps)
    assert steps[-1] <= 4
