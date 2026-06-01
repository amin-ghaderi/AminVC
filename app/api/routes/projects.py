"""Project routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_services
from app.api.errors import NotImplementedApiError
from app.api.mappers import project_response
from app.api.schemas.common import CreateProjectRequest, ProjectResponse
from app.api.services import ApplicationServices

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(services: ApplicationServices = Depends(get_services)) -> list[ProjectResponse]:
    ids = services.project_store.list_project_ids()
    return [
        project_response(services.project_store.load_project(project_id))
        for project_id in ids
    ]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    body: CreateProjectRequest,
    services: ApplicationServices = Depends(get_services),
) -> ProjectResponse:
    manifest = services.project_store.create_project(body.project_id, title=body.title)
    return project_response(manifest)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    services: ApplicationServices = Depends(get_services),
) -> ProjectResponse:
    return project_response(services.project_store.load_project(project_id))


@router.delete("/{project_id}")
def delete_project(project_id: str) -> None:
    del project_id
    raise NotImplementedApiError("Project delete is not implemented")
