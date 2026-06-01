"""Build routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.dependencies import get_services
from app.api.mappers import build_response, queue_job_response
from app.api.schemas.common import BuildResponse, CreateBuildRequest
from app.api.services import ApplicationServices

router = APIRouter(
    prefix="/projects/{project_id}/parts/{part_id}/builds",
    tags=["builds"],
)


@router.get("", response_model=list[BuildResponse])
def list_builds(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> list[BuildResponse]:
    builds = services.project_store.list_builds(project_id, part_id)
    return [build_response(b) for b in builds]


@router.post("", response_model=BuildResponse, status_code=201)
def create_build(
    project_id: str,
    part_id: str,
    body: CreateBuildRequest,
    services: ApplicationServices = Depends(get_services),
) -> BuildResponse:
    manifest = services.project_store.create_build(
        project_id,
        part_id,
        name=body.name,
        chunks=body.chunks,
        build_id=body.build_id,
    )
    return build_response(manifest)


@router.get("/{build_id}", response_model=BuildResponse)
def get_build(
    project_id: str,
    part_id: str,
    build_id: str,
    services: ApplicationServices = Depends(get_services),
) -> BuildResponse:
    manifest = services.project_store.load_build(project_id, part_id, build_id)
    return build_response(manifest)


@router.post("/{build_id}/queue")
def queue_build(
    project_id: str,
    part_id: str,
    build_id: str,
    services: ApplicationServices = Depends(get_services),
) -> dict[str, object]:
    services.project_store.load_build(project_id, part_id, build_id)
    item = services.queue.enqueue(
        project_id=project_id,
        part_id=part_id,
        job_type="build",
        chunk_id=None,
        job_id=build_id,
    )
    return queue_job_response(item)


@router.get("/{build_id}/download")
def download_build(
    project_id: str,
    part_id: str,
    build_id: str,
    services: ApplicationServices = Depends(get_services),
) -> FileResponse:
    build = services.project_store.load_build(project_id, part_id, build_id)
    path = services.project_store.part_layout(project_id, part_id).build_output_path(
        build.build_id
    )
    if not path.is_file():
        raise FileNotFoundError(f"Build output not found: {path}")
    return FileResponse(
        path,
        media_type="audio/wav",
        filename=f"{build_id}.wav",
    )
