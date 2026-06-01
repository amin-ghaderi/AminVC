"""Chunk, approval, and rebuild routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_services
from app.api.mappers import chunk_response
from app.api.schemas.common import ChunkResponse, UpdateChunkTextRequest
from app.api.services import ApplicationServices

router = APIRouter(
    prefix="/projects/{project_id}/parts/{part_id}/chunks",
    tags=["chunks"],
)


@router.get("", response_model=list[ChunkResponse])
def list_chunks(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> list[ChunkResponse]:
    chunks = services.project_store.list_chunks(project_id, part_id)
    return [chunk_response(c) for c in chunks]


@router.get("/{chunk_id}", response_model=ChunkResponse)
def get_chunk(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.project_store.load_chunk(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.put("/{chunk_id}/text", response_model=ChunkResponse)
def update_chunk_text(
    project_id: str,
    part_id: str,
    chunk_id: int,
    body: UpdateChunkTextRequest,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.rebuild.update_chunk_text(
        project_id,
        part_id,
        chunk_id,
        body.text,
    )
    return chunk_response(chunk)


@router.post("/{chunk_id}/approve-narration", response_model=ChunkResponse)
def approve_narration(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.approval.approve_narration(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.post("/{chunk_id}/approve-vc", response_model=ChunkResponse)
def approve_vc(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.approval.approve_vc(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.post("/{chunk_id}/unapprove-narration", response_model=ChunkResponse)
def unapprove_narration(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.approval.unapprove_narration(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.post("/{chunk_id}/unapprove-vc", response_model=ChunkResponse)
def unapprove_vc(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.approval.unapprove_vc(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.post("/{chunk_id}/rebuild-narration", response_model=ChunkResponse)
def rebuild_narration(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.rebuild.request_narration_rebuild(project_id, part_id, chunk_id)
    return chunk_response(chunk)


@router.post("/{chunk_id}/rebuild-vc", response_model=ChunkResponse)
def rebuild_vc(
    project_id: str,
    part_id: str,
    chunk_id: int,
    services: ApplicationServices = Depends(get_services),
) -> ChunkResponse:
    chunk = services.rebuild.request_vc_rebuild(project_id, part_id, chunk_id)
    return chunk_response(chunk)
