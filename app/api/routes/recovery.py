"""Recovery plan routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_services
from app.api.schemas.common import RestartPlanResponse, ResumePlanResponse
from app.api.services import ApplicationServices

router = APIRouter(
    prefix="/projects/{project_id}/parts/{part_id}",
    tags=["recovery"],
)


@router.get("/resume-plan", response_model=ResumePlanResponse)
def resume_plan(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> ResumePlanResponse:
    plan = services.recovery.create_resume_plan(project_id, part_id)
    return ResumePlanResponse(
        project_id=plan.project_id,
        part_id=plan.part_id,
        start_chunk=plan.start_chunk,
        remaining_chunks=list(plan.remaining_chunks),
    )


@router.get("/restart-plan", response_model=RestartPlanResponse)
def restart_plan(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> RestartPlanResponse:
    plan = services.recovery.create_restart_plan(project_id, part_id)
    return RestartPlanResponse(
        project_id=plan.project_id,
        part_id=plan.part_id,
        chunks=list(plan.chunks),
    )
