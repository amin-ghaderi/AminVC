"""E4.1 recovery event publishing helpers."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_RECOVERY_INTERRUPTED_DETECTED,
    EVENT_RECOVERY_RESTART_PLAN_CREATED,
    EVENT_RECOVERY_RESUME_PLAN_CREATED,
    create_event_envelope,
)
from app.contracts.recovery import RestartPlan, ResumePlan
from app.events.bus import EventBus
from app.events.helpers import safe_publish


def publish_interrupted_detected(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
    state: str,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_RECOVERY_INTERRUPTED_DETECTED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id, "state": state},
        ),
    )


def publish_resume_plan_created(
    event_bus: EventBus | None,
    plan: ResumePlan,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_RECOVERY_RESUME_PLAN_CREATED,
            project_id=plan.project_id,
            part_id=plan.part_id,
            payload={
                "start_chunk": plan.start_chunk,
                "remaining_chunks": list(plan.remaining_chunks),
            },
        ),
    )


def publish_restart_plan_created(
    event_bus: EventBus | None,
    plan: RestartPlan,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_RECOVERY_RESTART_PLAN_CREATED,
            project_id=plan.project_id,
            part_id=plan.part_id,
            payload={"chunks": list(plan.chunks)},
        ),
    )
