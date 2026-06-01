"""Queue routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from app.api.dependencies import get_services
from app.api.mappers import queue_job_response, queue_snapshot_response
from app.api.schemas.common import (
    QueueJobRequest,
    QueueResumeRequest,
    QueueSnapshotResponse,
)
from app.api.services import ApplicationServices

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=QueueSnapshotResponse)
def queue_snapshot(
    services: ApplicationServices = Depends(get_services),
) -> QueueSnapshotResponse:
    snap = services.queue.snapshot()
    return QueueSnapshotResponse(**queue_snapshot_response(snap))


@router.post("/narration")
def queue_narration(
    body: QueueJobRequest,
    services: ApplicationServices = Depends(get_services),
) -> dict[str, object]:
    item = services.queue.enqueue(
        project_id=body.project_id,
        part_id=body.part_id,
        job_type="narration",
        chunk_id=body.chunk_id,
    )
    return queue_job_response(item)


@router.post("/vc")
def queue_vc(
    body: QueueJobRequest,
    services: ApplicationServices = Depends(get_services),
) -> dict[str, object]:
    item = services.queue.enqueue(
        project_id=body.project_id,
        part_id=body.part_id,
        job_type="vc",
        chunk_id=body.chunk_id,
    )
    return queue_job_response(item)


@router.post("/resume")
def queue_resume(
    body: QueueResumeRequest,
    services: ApplicationServices = Depends(get_services),
) -> list[dict[str, object]]:
    job_type: Literal["narration", "vc"] = (
        "vc" if body.job_type == "vc" else "narration"
    )
    plan = services.recovery.create_resume_plan(body.project_id, body.part_id)
    items = services.queue.enqueue_resume_plan(plan, job_type=job_type)
    return [queue_job_response(item) for item in items]


@router.post("/cancel/{job_id}")
def cancel_job(
    job_id: str,
    services: ApplicationServices = Depends(get_services),
) -> dict[str, object]:
    item = services.queue.cancel(job_id)
    return queue_job_response(item)
